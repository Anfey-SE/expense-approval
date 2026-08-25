package com.sandy.expense.integration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import tools.jackson.databind.JsonNode;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

/**
 * The whole approval path, driven the way the SPA drives it, with the audit trail read back out of
 * Postgres at the end.
 */
class ApprovalWorkflowIntegrationTest extends HttpIntegrationTest {

    private JsonNode fetch(String token, long id) throws Exception {
        String body =
                mvc.perform(get("/api/requests/" + id).header("Authorization", "Bearer " + token))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        return json.readTree(body);
    }

    private void decide(String token, long id, String action, String comment) throws Exception {
        mvc.perform(
                        post("/api/requests/" + id + "/" + action)
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(json.writeValueAsString(java.util.Map.of("comment", comment))))
                .andExpect(status().isOk());
    }

    @Test
    void draftToFinanceApprovedLeavesOneAuditRowPerTransition() throws Exception {
        String alice = tokenFor("alice@acme.com"); // EMPLOYEE, Engineering
        String bob = tokenFor("bob@acme.com"); // MANAGER, Engineering
        String fiona = tokenFor("fiona@acme.com"); // FINANCE

        long id = createDraft(alice, "Team offsite");
        assertThat(fetch(alice, id).get("status").asText()).isEqualTo("DRAFT");

        submit(alice, id);
        assertThat(fetch(alice, id).get("status").asText()).isEqualTo("SUBMITTED");

        decide(bob, id, "approve", "looks reasonable");
        assertThat(fetch(alice, id).get("status").asText()).isEqualTo("MANAGER_APPROVED");

        decide(fiona, id, "approve", "budget confirmed");

        JsonNode finished = fetch(alice, id);
        assertThat(finished.get("status").asText()).isEqualTo("FINANCE_APPROVED");

        // Three transitions happened, so the append-only trail holds exactly three rows, in order,
        // each naming who acted and what the status was on either side of their decision.
        JsonNode trail = finished.get("approvals");
        assertThat(trail).hasSize(3);
        assertThat(trail.get(0).get("action").asText()).isEqualTo("SUBMIT");
        assertThat(trail.get(0).get("toStatus").asText()).isEqualTo("SUBMITTED");
        assertThat(trail.get(1).get("actorName").asText()).isEqualTo("Bob Manager");
        assertThat(trail.get(1).get("fromStatus").asText()).isEqualTo("SUBMITTED");
        assertThat(trail.get(1).get("toStatus").asText()).isEqualTo("MANAGER_APPROVED");
        assertThat(trail.get(2).get("actorName").asText()).isEqualTo("Fiona Finance");
        assertThat(trail.get(2).get("toStatus").asText()).isEqualTo("FINANCE_APPROVED");
        assertThat(trail.get(2).get("comment").asText()).isEqualTo("budget confirmed");

        // Terminal state: nobody is awaiting a decision, so a further approval is a 409 rather than
        // a fourth row.
        mvc.perform(
                        post("/api/requests/" + id + "/approve")
                                .header("Authorization", "Bearer " + fiona)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"comment\":\"again\"}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("NOT_PENDING"));
    }

    @Test
    void aManagerHoldingTheRightRoleStillCannotDecideOnTheirOwnRequest() throws Exception {
        // Bob clears the endpoint gate (MANAGER), owns the stage (SUBMITTED), and is in the right
        // department — every check except the last one passes. Self-approval is the case the role
        // gate alone cannot catch, which is the reason the service checks again.
        String bob = tokenFor("bob@acme.com");
        long hisOwn = submittedRequest(bob, "Bob's own laptop");

        mvc.perform(
                        post("/api/requests/" + hisOwn + "/approve")
                                .header("Authorization", "Bearer " + bob)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"comment\":\"self-serve\"}"))
                .andExpect(status().isForbidden());

        assertThat(fetch(bob, hisOwn).get("status").asText()).isEqualTo("SUBMITTED");
    }
}

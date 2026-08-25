package com.sandy.expense.integration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import tools.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/**
 * The inner layer of authorization: who each role is allowed to see once the endpoint gate has let
 * them through. {@code GET /api/requests} is a single endpoint that every role may call, so the
 * scoping is entirely in the query the service picks — EMPLOYEE=own, MANAGER=department,
 * FINANCE=all.
 *
 * <p>These assertions are deliberately about the <em>properties</em> of what comes back, never
 * about row counts: the Postgres container is shared by every test class in this package and rows
 * from other tests persist, so any exact total would be a function of test ordering.
 */
class RoleScopedListingIntegrationTest extends HttpIntegrationTest {

    /** Every summary row on page 0, following pagination to the end. */
    private List<JsonNode> allRows(String token) throws Exception {
        List<JsonNode> rows = new ArrayList<>();
        int page = 0;
        while (true) {
            String body =
                    mvc.perform(
                                    get("/api/requests")
                                            .param("page", String.valueOf(page))
                                            .param("size", "100")
                                            .header("Authorization", "Bearer " + token))
                            .andExpect(status().isOk())
                            .andReturn()
                            .getResponse()
                            .getContentAsString();
            JsonNode json = this.json.readTree(body);
            json.get("content").forEach(rows::add);
            if (++page >= json.get("totalPages").asInt()) {
                return rows;
            }
        }
    }

    @Test
    void anEmployeeSeesOnlyTheirOwnRequests() throws Exception {
        String alice = tokenFor("alice@acme.com"); // EMPLOYEE, Engineering
        createDraft(alice, "Alice sees this");
        createDraft(tokenFor("carol@acme.com"), "Carol's, in another department");

        assertThat(allRows(alice))
                .isNotEmpty()
                .allSatisfy(r -> assertThat(r.get("requesterName").asText()).isEqualTo("Alice Employee"));
    }

    @Test
    void aManagerSeesTheirWholeDepartmentButNotAnother() throws Exception {
        String bob = tokenFor("bob@acme.com"); // MANAGER, Engineering
        createDraft(tokenFor("alice@acme.com"), "Engineering, by a report");
        createDraft(tokenFor("carol@acme.com"), "Sales, none of Bob's business");

        List<JsonNode> rows = allRows(bob);
        assertThat(rows)
                .isNotEmpty()
                .allSatisfy(r -> assertThat(r.get("departmentName").asText()).isEqualTo("Engineering"));
        // A manager's scope is the department, not their own submissions: someone else's row is here.
        assertThat(rows).anySatisfy(r -> assertThat(r.get("requesterName").asText()).isEqualTo("Alice Employee"));
    }

    @Test
    void financeSeesEveryDepartment() throws Exception {
        createDraft(tokenFor("alice@acme.com"), "Engineering row");
        createDraft(tokenFor("carol@acme.com"), "Sales row");

        List<JsonNode> rows = allRows(tokenFor("fiona@acme.com")); // FINANCE
        assertThat(rows).extracting(r -> r.get("departmentName").asText())
                .contains("Engineering", "Sales");
    }

    @Test
    void anotherDepartmentsRequestReadsAs404SoItsExistenceIsNotLeaked() throws Exception {
        // assertCanView answers 404 rather than 403 on purpose. 403 would confirm that a request
        // with this id exists and belongs to someone else, which is itself information.
        long carolsRequest = createDraft(tokenFor("carol@acme.com"), "Sales-only");

        mvc.perform(
                        get("/api/requests/" + carolsRequest)
                                .header("Authorization", "Bearer " + tokenFor("alice@acme.com")))
                .andExpect(status().isNotFound());

        // Finance may read the very same row, which is what makes the 404 above a scoping decision
        // rather than the request simply not being there.
        mvc.perform(
                        get("/api/requests/" + carolsRequest)
                                .header("Authorization", "Bearer " + tokenFor("fiona@acme.com")))
                .andExpect(status().isOk());
    }
}

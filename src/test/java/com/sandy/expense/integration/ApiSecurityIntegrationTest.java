package com.sandy.expense.integration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

/**
 * The outer layer of authorization: what the filter chain and the {@code @PreAuthorize} gates
 * reject before any service code runs.
 *
 * <p>The distinction this class exists to prove is the one a mocked test cannot: several of these
 * calls use an id that does not exist. If the request were reaching the service it would come back
 * 404. Getting 403 instead is the evidence that the endpoint gate stopped it first.
 */
class ApiSecurityIntegrationTest extends HttpIntegrationTest {

    /** An id no seeded row will ever have — see the class note on 403-before-404. */
    private static final long NO_SUCH_REQUEST = 999_999L;

    @Test
    void aProtectedEndpointWithoutATokenIs401() throws Exception {
        mvc.perform(get("/api/requests"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("UNAUTHORIZED"));
    }

    @Test
    void aMalformedBearerTokenIs401RatherThan403() throws Exception {
        // JwtService.parse returns null for a token it cannot verify, so the SecurityContext stays
        // empty and the request is unauthenticated — not authenticated-but-forbidden. The SPA keys
        // its "session expired" redirect off 401, so the difference is user-visible.
        mvc.perform(get("/api/requests").header("Authorization", "Bearer not-a-real-token"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("UNAUTHORIZED"));
    }

    @Test
    void anEmployeeIsStoppedAtTheApproveEndpointByTheRoleGate() throws Exception {
        String alice = tokenFor("alice@acme.com"); // EMPLOYEE
        mvc.perform(
                        post("/api/requests/" + NO_SUCH_REQUEST + "/approve")
                                .header("Authorization", "Bearer " + alice)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"comment\":\"let me through\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void anEmployeeIsStoppedAtTheRejectEndpointByTheRoleGate() throws Exception {
        String alice = tokenFor("alice@acme.com");
        mvc.perform(
                        post("/api/requests/" + NO_SUCH_REQUEST + "/reject")
                                .header("Authorization", "Bearer " + alice)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"comment\":\"nope\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void aManagerPassesTheRoleGateAndIsJudgedOnTheRequestInstead() throws Exception {
        // Same call, same nonexistent id, different role: this one clears the endpoint gate and is
        // decided by the service, which cannot find the request. 404 here is what makes the two
        // 403s above meaningful rather than incidental.
        String bob = tokenFor("bob@acme.com"); // MANAGER
        mvc.perform(
                        post("/api/requests/" + NO_SUCH_REQUEST + "/approve")
                                .header("Authorization", "Bearer " + bob)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"comment\":\"ok\"}"))
                .andExpect(status().isNotFound());
    }

    @Test
    void registrationIgnoresAClientSuppliedRoleAndAlwaysCreatesAnEmployee() throws Exception {
        // RegisterRequest has no role field on purpose. Sending one anyway must not promote the
        // account: if it did, anyone could self-register as FINANCE and approve every request in
        // the company, and every check in this class would be decoration.
        String email = "escalation-" + System.nanoTime() + "@acme.com";
        String body =
                json.writeValueAsString(
                        Map.of(
                                "email", email,
                                "password", "password123",
                                "fullName", "Mallory Escalation",
                                "role", "FINANCE"));

        String created =
                mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON).content(body))
                        .andExpect(status().isCreated())
                        .andExpect(jsonPath("$.user.role").value("EMPLOYEE"))
                        .andReturn()
                        .getResponse()
                        .getContentAsString();

        // And the token minted for that account carries the same role the database gave it.
        String token = json.readTree(created).get("token").asText();
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.role").value("EMPLOYEE"));
    }

    @Test
    void loginIssuesATokenThatIdentifiesTheCallerToEveryOtherEndpoint() throws Exception {
        String fiona = tokenFor("fiona@acme.com");
        assertThat(fiona).as("login must return a non-empty token").isNotBlank();

        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + fiona))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("fiona@acme.com"))
                .andExpect(jsonPath("$.role").value("FINANCE"));
    }
}

package com.sandy.expense.integration;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import tools.jackson.databind.ObjectMapper;
import com.sandy.expense.web.dto.AuthDtos.LoginRequest;
import com.sandy.expense.web.dto.ExpenseDtos.CreateRequest;
import com.sandy.expense.web.dto.ExpenseDtos.ItemInput;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Base for tests that drive the application over HTTP rather than by calling services directly.
 *
 * <p>The service-level tests elsewhere hand {@link com.sandy.expense.security.AppUserPrincipal}
 * straight to {@link com.sandy.expense.service.ExpenseService}, which skips two things that are
 * part of the authorization story: the filter chain that turns a Bearer token into that principal
 * in the first place, and the {@code @PreAuthorize} gates on the controller methods. A test that
 * calls the service directly cannot tell the difference between "the endpoint is protected" and
 * "the endpoint is wide open but the service happens to check". Going through MockMvc with a real
 * token, against the real Postgres from {@link PostgresIntegrationTest}, exercises both layers.
 *
 * <p>All demo accounts seeded by {@code DataSeeder} share the password below.
 */
@AutoConfigureMockMvc
public abstract class HttpIntegrationTest extends PostgresIntegrationTest {

    protected static final String SEED_PASSWORD = "password123";

    @Autowired protected MockMvc mvc;
    @Autowired protected ObjectMapper json;

    /** Logs a seeded user in through the real endpoint and returns their Bearer token. */
    protected String tokenFor(String email) throws Exception {
        String body =
                mvc.perform(
                                post("/api/auth/login")
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(json.writeValueAsString(new LoginRequest(email, SEED_PASSWORD))))
                        .andExpect(status().isOk())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        return json.readTree(body).get("token").asText();
    }

    /** Creates a one-line DRAFT request as the token's owner and returns its id. */
    protected long createDraft(String token, String title) throws Exception {
        CreateRequest body =
                new CreateRequest(
                        title,
                        "created by an integration test",
                        "USD",
                        List.of(new ItemInput("Line item", "TRAVEL", new BigDecimal("100.00"), LocalDate.now())));
        String res =
                mvc.perform(
                                post("/api/requests")
                                        .header("Authorization", "Bearer " + token)
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(json.writeValueAsString(body)))
                        .andExpect(status().isCreated())
                        .andReturn()
                        .getResponse()
                        .getContentAsString();
        return json.readTree(res).get("id").asLong();
    }

    /** Moves a DRAFT to SUBMITTED as its owner. */
    protected void submit(String token, long id) throws Exception {
        mvc.perform(post("/api/requests/" + id + "/submit").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    /** Creates and submits in one step — the usual starting point for approval tests. */
    protected long submittedRequest(String token, String title) throws Exception {
        long id = createDraft(token, title);
        submit(token, id);
        return id;
    }
}

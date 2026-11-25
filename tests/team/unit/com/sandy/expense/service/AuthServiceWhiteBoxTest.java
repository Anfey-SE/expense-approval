package com.sandy.expense.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.sandy.expense.domain.Department;
import com.sandy.expense.domain.Role;
import com.sandy.expense.domain.User;
import com.sandy.expense.repo.DepartmentRepository;
import com.sandy.expense.repo.UserRepository;
import com.sandy.expense.security.JwtService;
import com.sandy.expense.web.dto.AuthDtos.AuthResponse;
import com.sandy.expense.web.dto.AuthDtos.LoginRequest;
import com.sandy.expense.web.dto.AuthDtos.RegisterRequest;
import com.sandy.expense.web.dto.AuthDtos.UserView;
import com.sandy.expense.web.error.ApiException;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;

/** Member 1 white-box tests for {@link AuthService}: every branch of register / login / me. */
@ExtendWith(MockitoExtension.class)
class AuthServiceWhiteBoxTest {

    @Mock UserRepository users;
    @Mock DepartmentRepository departments;
    @Mock PasswordEncoder encoder;
    @Mock JwtService jwt;
    @Mock AuthenticationManager authManager;
    @InjectMocks AuthService service;

    // ---- register ----

    @Test
    void register_emailAlreadyTaken_isConflict_andNothingSaved() {
        when(users.existsByEmail("a@acme.com")).thenReturn(true);
        assertThatThrownBy(() -> service.register(new RegisterRequest("a@acme.com", "password123", "A", null)))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("EMAIL_TAKEN");
        verify(users, never()).save(any());
    }

    @Test
    void register_withoutDepartment_createsEmployeeWithNullDepartment() {
        when(users.existsByEmail(anyString())).thenReturn(false);
        when(encoder.encode("password123")).thenReturn("hash");
        when(jwt.issue(any())).thenReturn("tok");
        when(jwt.ttlSeconds()).thenReturn(7200L);

        AuthResponse res = service.register(new RegisterRequest("n@acme.com", "password123", "New", null));

        ArgumentCaptor<User> saved = ArgumentCaptor.forClass(User.class);
        verify(users).save(saved.capture());
        assertThat(saved.getValue().getRole()).isEqualTo(Role.EMPLOYEE);
        assertThat(saved.getValue().getDepartment()).isNull();
        assertThat(saved.getValue().getPasswordHash()).isEqualTo("hash");
        assertThat(res.token()).isEqualTo("tok");
        assertThat(res.tokenType()).isEqualTo("Bearer");
        assertThat(res.expiresInSeconds()).isEqualTo(7200L);
        assertThat(res.user().departmentId()).isNull();
        assertThat(res.user().departmentName()).isNull();
    }

    @Test
    void register_withKnownDepartment_attachesIt() {
        Department eng = new Department("Engineering");
        eng.setId(1L);
        when(users.existsByEmail(anyString())).thenReturn(false);
        when(departments.findById(1L)).thenReturn(Optional.of(eng));
        when(encoder.encode(anyString())).thenReturn("hash");
        when(jwt.issue(any())).thenReturn("tok");

        AuthResponse res = service.register(new RegisterRequest("n@acme.com", "password123", "New", 1L));

        assertThat(res.user().departmentId()).isEqualTo(1L);
        assertThat(res.user().departmentName()).isEqualTo("Engineering");
    }

    @Test
    void register_withUnknownDepartment_isBadRequest_andNothingSaved() {
        when(users.existsByEmail(anyString())).thenReturn(false);
        when(departments.findById(99L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.register(new RegisterRequest("n@acme.com", "password123", "New", 99L)))
                .isInstanceOf(ApiException.class)
                .extracting(e -> ((ApiException) e).getCode())
                .isEqualTo("BAD_DEPARTMENT");
        verify(users, never()).save(any());
    }

    @Test
    void register_persistsEmailAndFullName() {
        when(users.existsByEmail("newuser@acme.com")).thenReturn(false);
        when(encoder.encode("password123")).thenReturn("hash");
        when(jwt.issue(any())).thenReturn("tok");
        when(jwt.ttlSeconds()).thenReturn(7200L);

        AuthResponse res =
                service.register(new RegisterRequest("newuser@acme.com", "password123", "New User", null));

        ArgumentCaptor<User> saved = ArgumentCaptor.forClass(User.class);
        verify(users).save(saved.capture());
        assertThat(saved.getValue().getEmail()).isEqualTo("newuser@acme.com");
        assertThat(saved.getValue().getFullName()).isEqualTo("New User");
        assertThat(res.user().email()).isEqualTo("newuser@acme.com");
        assertThat(res.user().fullName()).isEqualTo("New User");
    }

    // ---- login ----

    @Test
    void login_success_returnsTokenForTheStoredUser() {
        User u = user(5L, "u@acme.com", Role.MANAGER);
        when(users.findByEmail("u@acme.com")).thenReturn(Optional.of(u));
        when(jwt.issue(u)).thenReturn("tok");
        when(jwt.ttlSeconds()).thenReturn(60L);

        AuthResponse res = service.login(new LoginRequest("u@acme.com", "pw"));

        assertThat(res.token()).isEqualTo("tok");
        assertThat(res.user().role()).isEqualTo(Role.MANAGER);
    }

    @Test
    void login_badCredentials_is401_andNoTokenIssued() {
        when(authManager.authenticate(any())).thenThrow(new BadCredentialsException("bad"));
        assertThatThrownBy(() -> service.login(new LoginRequest("u@acme.com", "wrong")))
                .isInstanceOf(ApiException.class)
                .satisfies(e -> {
                    ApiException ex = (ApiException) e;
                    assertThat(ex.getStatus().value()).isEqualTo(401);
                    assertThat(ex.getCode()).isEqualTo("BAD_CREDENTIALS");
                });
        verify(jwt, never()).issue(any());
    }

    @Test
    void login_authenticatedButUserRowMissing_isNotFound() {
        when(users.findByEmail("ghost@acme.com")).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.login(new LoginRequest("ghost@acme.com", "pw")))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("User not found");
    }

    @Test
    void login_passesEmailAndPasswordToAuthenticationManager() {
        User u = user(6L, "login@acme.com", Role.EMPLOYEE);
        when(users.findByEmail("login@acme.com")).thenReturn(Optional.of(u));
        when(jwt.issue(u)).thenReturn("tok");
        when(jwt.ttlSeconds()).thenReturn(60L);

        service.login(new LoginRequest("login@acme.com", "secret-pw"));

        ArgumentCaptor<Authentication> authCap = ArgumentCaptor.forClass(Authentication.class);
        verify(authManager).authenticate(authCap.capture());
        assertThat(authCap.getValue()).isInstanceOf(UsernamePasswordAuthenticationToken.class);
        assertThat(authCap.getValue().getPrincipal()).isEqualTo("login@acme.com");
        assertThat(authCap.getValue().getCredentials()).isEqualTo("secret-pw");
    }

    // ---- me ----

    @Test
    void me_existingUser_returnsView() {
        when(users.findById(5L)).thenReturn(Optional.of(user(5L, "u@acme.com", Role.FINANCE)));
        UserView v = service.me(5L);
        assertThat(v.email()).isEqualTo("u@acme.com");
        assertThat(v.role()).isEqualTo(Role.FINANCE);
    }

    @Test
    void me_unknownUser_isNotFound() {
        when(users.findById(404L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.me(404L)).isInstanceOf(ApiException.class);
    }

    private static User user(long id, String email, Role role) {
        User u = new User();
        u.setId(id);
        u.setEmail(email);
        u.setFullName("Name");
        u.setPasswordHash("h");
        u.setRole(role);
        return u;
    }
}

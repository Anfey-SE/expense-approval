package com.sandy.expense.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.sandy.expense.domain.Department;
import com.sandy.expense.domain.Role;
import com.sandy.expense.domain.User;
import io.jsonwebtoken.Claims;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

/** White-box unit tests for {@link JwtService} and {@link AppUserPrincipal}. */
class SecurityWhiteBoxTest {

    private static final String SECRET_32 = "0123456789abcdef0123456789abcdef";
    private static final String OTHER_SECRET_32 = "fedcba9876543210fedcba9876543210";

    private static User user(Long id, String email, Role role, Department dept) {
        User u = new User();
        u.setId(id);
        u.setEmail(email);
        u.setPasswordHash("hashed");
        u.setFullName("Test User");
        u.setRole(role);
        u.setDepartment(dept);
        return u;
    }

    // ---- JwtService: secret-length and TTL rules ----

    @Test
    void jwtService_nullOrBlankSecret_generatesRandomDevKeyAndWorks() {
        JwtService fromNull = new JwtService(null, 30);
        JwtService fromBlank = new JwtService("   ", 30);
        User alice = user(1L, "alice@acme.com", Role.EMPLOYEE, null);

        String token = fromNull.issue(alice);
        Claims claims = fromNull.parse(token);
        assertThat(claims).isNotNull();
        assertThat(claims.getSubject()).isEqualTo("1");
        // Random keys differ between instances
        assertThat(fromBlank.parse(token)).isNull();
    }

    @Test
    void jwtService_shortSecretBelow32Bytes_throwsIllegalState() {
        String short31 = "a".repeat(31);
        assertThat(short31.getBytes(StandardCharsets.UTF_8)).hasSize(31);

        assertThatThrownBy(() -> new JwtService(short31, 60))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("at least 32 bytes")
                .hasMessageContaining("got 31");
    }

    @Test
    void jwtService_ttlSeconds_convertsMinutesToSeconds() {
        JwtService jwt = new JwtService(SECRET_32, 120);
        assertThat(jwt.ttlSeconds()).isEqualTo(7200L);
    }

    // ---- JwtService: issue and parse round trip + claims ----

    @Test
    void jwtService_issueAndParse_withDepartment_roundTripsAllClaims() {
        JwtService jwt = new JwtService(SECRET_32, 60);
        Department eng = new Department("Engineering");
        eng.setId(10L);
        User alice = user(42L, "alice@acme.com", Role.MANAGER, eng);

        String token = jwt.issue(alice);
        Claims claims = jwt.parse(token);

        assertThat(claims).isNotNull();
        assertThat(claims.getSubject()).isEqualTo("42");
        assertThat(claims.get("email", String.class)).isEqualTo("alice@acme.com");
        assertThat(claims.get("role", String.class)).isEqualTo("MANAGER");
        assertThat(claims.get("dept", Long.class)).isEqualTo(10L);
        assertThat(claims.getIssuedAt()).isNotNull();
        assertThat(claims.getExpiration()).isAfter(claims.getIssuedAt());
    }

    @Test
    void jwtService_issueAndParse_withoutDepartment_omitsDeptClaim() {
        JwtService jwt = new JwtService(SECRET_32, 60);
        User fiona = user(5L, "fiona@acme.com", Role.FINANCE, null);

        Claims claims = jwt.parse(jwt.issue(fiona));

        assertThat(claims).isNotNull();
        assertThat(claims.getSubject()).isEqualTo("5");
        assertThat(claims.get("role", String.class)).isEqualTo("FINANCE");
        assertThat(claims.get("dept")).isNull();
    }

    // ---- JwtService: rejection cases ----

    @Test
    void jwtService_expiredToken_returnsNull() {
        JwtService expiredIssuer = new JwtService(SECRET_32, -1);
        JwtService verifier = new JwtService(SECRET_32, 60);
        User alice = user(1L, "alice@acme.com", Role.EMPLOYEE, null);

        String expiredToken = expiredIssuer.issue(alice);
        assertThat(verifier.parse(expiredToken)).isNull();
    }

    @Test
    void jwtService_tamperedSignature_returnsNull() {
        JwtService jwt = new JwtService(SECRET_32, 60);
        String token = jwt.issue(user(1L, "alice@acme.com", Role.EMPLOYEE, null));
        int lastDot = token.lastIndexOf('.');
        char lastChar = token.charAt(token.length() - 1);
        char flipped = (lastChar == 'a') ? 'b' : 'a';
        String tampered = token.substring(0, lastDot + 1) + token.substring(lastDot + 1, token.length() - 1) + flipped;

        assertThat(jwt.parse(tampered)).isNull();
    }

    @Test
    void jwtService_wrongSecret_returnsNull() {
        JwtService issuer = new JwtService(SECRET_32, 60);
        JwtService other = new JwtService(OTHER_SECRET_32, 60);
        String token = issuer.issue(user(1L, "alice@acme.com", Role.EMPLOYEE, null));

        assertThat(other.parse(token)).isNull();
    }

    @Test
    void jwtService_malformedOrNullToken_returnsNull() {
        JwtService jwt = new JwtService(SECRET_32, 60);

        assertThat(jwt.parse("not-a-jwt")).isNull();
        assertThat(jwt.parse("")).isNull();
        assertThat(jwt.parse(null)).isNull();
    }

    // ---- AppUserPrincipal ----

    @Test
    void principal_fromUserWithDepartment_mapsFieldsAndRoleAuthority() {
        Department sales = new Department("Sales");
        sales.setId(2L);
        User carol = user(3L, "carol@acme.com", Role.EMPLOYEE, sales);

        AppUserPrincipal p = AppUserPrincipal.fromUser(carol);

        assertThat(p.getUserId()).isEqualTo(3L);
        assertThat(p.getUsername()).isEqualTo("carol@acme.com");
        assertThat(p.getPassword()).isEqualTo("hashed");
        assertThat(p.getRole()).isEqualTo(Role.EMPLOYEE);
        assertThat(p.getDepartmentId()).isEqualTo(2L);
        assertThat(p.getAuthorities())
                .extracting("authority")
                .containsExactly("ROLE_EMPLOYEE");
        assertThat(p.isAccountNonExpired()).isTrue();
        assertThat(p.isAccountNonLocked()).isTrue();
        assertThat(p.isCredentialsNonExpired()).isTrue();
        assertThat(p.isEnabled()).isTrue();
    }

    @Test
    void principal_fromUserWithoutDepartment_hasNullDepartmentIdAndFinanceAuthority() {
        User fiona = user(5L, "fiona@acme.com", Role.FINANCE, null);

        AppUserPrincipal p = AppUserPrincipal.fromUser(fiona);

        assertThat(p.getDepartmentId()).isNull();
        assertThat(p.getAuthorities())
                .extracting("authority")
                .containsExactly("ROLE_FINANCE");
    }
}

package org.library.usersbe.model;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class UserTest {

    @Test
    @DisplayName("Default constructor → generates UUID automatically")
    void defaultConstructor_generatesUUID() {
        User user = new User();
        assertNotNull(user.getUuid());
    }

    @Test
    @DisplayName("Two users → have different UUIDs")
    void twoUsers_differentUUIDs() {
        User u1 = new User();
        User u2 = new User();
        assertNotEquals(u1.getUuid(), u2.getUuid());
    }

    @Test
    @DisplayName("All-args constructor → sets all fields")
    void allArgsConstructor_setsAllFields() {
        UUID uuid = UUID.randomUUID();
        User user = new User(uuid, "alice", "pass123", "Alice", "Smith", "alice@test.com", "123456", Role.CLIENT);

        assertEquals(uuid, user.getUuid());
        assertEquals("alice", user.getUsername());
        assertEquals("pass123", user.getPassword());
        assertEquals("Alice", user.getFirstName());
        assertEquals("Smith", user.getLastName());
        assertEquals("alice@test.com", user.getEmail());
        assertEquals("123456", user.getPhone());
        assertEquals(Role.CLIENT, user.getRole());
    }

    @Test
    @DisplayName("Setters and getters work correctly")
    void settersAndGetters() {
        User user = new User();
        user.setUsername("bob");
        user.setPassword("secret");
        user.setFirstName("Bob");
        user.setLastName("Jones");
        user.setEmail("bob@test.com");
        user.setPhone("999888");
        user.setRole(Role.ADMIN);

        assertEquals("bob", user.getUsername());
        assertEquals("secret", user.getPassword());
        assertEquals("Bob", user.getFirstName());
        assertEquals("Jones", user.getLastName());
        assertEquals("bob@test.com", user.getEmail());
        assertEquals("999888", user.getPhone());
        assertEquals(Role.ADMIN, user.getRole());
    }
}


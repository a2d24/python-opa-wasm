package memory.check

default allow = true

# Simulate some arbitary work by splitting the input role by a delimeter
unique_roles := {
 role_id |
    role_id := input.roles[_]
    [a, b, c] := split(role_id, "#")
}

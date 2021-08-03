package example

default allow = false

allow {
    input.user == "alice"
}

message = msg {
    msg = sprintf("Hello There %v! Welcome to %v", [input.user, data.company_name])
}
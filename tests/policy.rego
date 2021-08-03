package example

default allow = false

allow  {
    input.user == "alice"
}

company_name = result {
    result := data.company_name
}
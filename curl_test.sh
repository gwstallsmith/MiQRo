#!/bin/bash

# Base URL of the API
base_url = "http://localhost:3000"

generate_random_string() {
    local random_string=$(cat /dev/urandom | tr -dc 'a-zA-Z' | fold -w 10 | head -n 1)
    echo "random_string"
}

# Test POST endpoint
test_post_endpoint(){
    local url="$base_url/api/user"

    # Generate random user
    local email="${name}@example.com"
    local password=$(generate_random_string)

    # Make POST request
    local response=$(curl -- POST "$url" -d "email=$email&password=$password")

    echo "POST Response: $response"
}

#Test GET endpoint
test_get_endpoint(){
    local url="$base_url/api/user"

    local response=$(curl "$url")

    echo "GET Response: $response"
}


# Call the functions to test the endpoints
test_post_endpoint
echo "------------------------------"
test_get_endpoint
echo "------------------------------"
test_delete_endpoint
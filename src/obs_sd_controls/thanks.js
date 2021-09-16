function paramsToObject(entries) {
    const result = {};
    for(const [key, value] of entries) {
        result[key] = value;
    };
    return result;
}

function post(data) {
    return fetch('http://localhost:8000/', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
    });
}

async function post_tokens(tokens, StatusMessage) {
    const response = await post(tokens)
    if (response.status == 202) {
        StatusMessage.innerHTML = "Success!";
    } else {
        StatusMessage.innerHTML = "Something went wrong"
    }
    return response
}

function main() {
    const params = new URLSearchParams(document.location.hash);
    const keyVars = paramsToObject(params.entries());
    const StatusMessage = document.getElementById("status_message");
    const response = post_tokens(keyVars, StatusMessage);
    console.log(response);
}

main()

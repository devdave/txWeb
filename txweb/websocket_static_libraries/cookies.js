
export {parse_cookies};

function parse_cookies(raw_cookies) {

    raw_cookies = raw_cookies.split(";")
    let cookies = {}

    if (raw_cookies == "") {
        return cookies;
    }

    for(let raw_cookie of raw_cookies) {
        raw_cookie = raw_cookie.trim();
        let key_name, key_value
        [key_name, key_value] = raw_cookie.split("=", 2);
        cookies[key_name.trim()] = key_value.trim();
        console.log(key_name, key_value);
    }

    return cookies;
}

function set_cookie(name, value, exp) {
    alert("no");  //set cookies via server side
}
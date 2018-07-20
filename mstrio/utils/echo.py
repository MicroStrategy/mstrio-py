def echo_response(response):
    print("HTTP %i - %s, Message %s" % (response.status_code, response.reason, response.text))

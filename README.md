- Run both scripts to simulate the two ends.
- Run them multiple times to simulate many servers and clients.
- Check the scripts to see how to run them.

#Features -
- Threaded Proxy server
- The proxy keeps a count of the requests that are made. If a URL is requested more than 3 times in 5 minutes, the response from the server is cached. In case of any further requests for the same, the proxy utilises the “If Modified Since” header to check if any updates have been made, and if not, then it serves the response from
the cache. The cache has a memory limit of 3 responses.
- The proxy supports blacklisting of certain outside domains. These addresses should be stored in “black-list.txt”. If the request wants a page that belongs to one of these, then, it returns an error page.
- Proxy handles authentication using Basic Access Authentication and appropriate headers to allow access to black-listed sites as well. The authentication is username/password based, and can be assumed to be stored on the proxy server.

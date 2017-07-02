from twisted.python import log
from twisted.web import http, proxy


class ProxyClient(proxy.ProxyClient):
    def handleHeader(self, key, value):
        """
        This method modify headers. Check if header "Access-Control-Allow-Origin" exists and add/modify it
        """
        if not self.father.responseHeaders.hasHeader(b"access-control-allow-origin"):
            self.father.responseHeaders.addRawHeader(b"access-control-allow-origin", b"*")
        elif key == b"access-control-allow-origin" and value != b"*":
            value = b"*"
        proxy.ProxyClient.handleHeader(self, key, value)


class ProxyClientFactory(proxy.ProxyClientFactory):
    protocol = ProxyClient


class ProxyRequest(proxy.ProxyRequest):
    protocols = dict(http=ProxyClientFactory)


class Proxy(proxy.Proxy):
    requestFactory = ProxyRequest


class ProxyFactory(http.HTTPFactory):
    protocol = Proxy


portstr = "tcp:8080:interface=localhost"  # serve on localhost:8080

if __name__ == '__main__':
    import sys
    from twisted.internet import endpoints, reactor


    def shutdown(reason, reactor, stopping=[]):
        """Stop the reactor."""
        if stopping: return
        stopping.append(True)
        if reason:
            log.msg(reason.value)
        reactor.callWhenRunning(reactor.stop)


    log.startLogging(sys.stdout)
    endpoint = endpoints.serverFromString(reactor, portstr)
    d = endpoint.listen(ProxyFactory())
    d.addErrback(shutdown, reactor)
    reactor.run()
else:  # $ twistd -ny server.py
    from twisted.application import service, strports

    application = service.Application("proxy_modify_request")
    strports.service(portstr, ProxyFactory()).setServiceParent(application)

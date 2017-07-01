from pprint import pprint

from twisted.python import log
from twisted.web import http, proxy
from twisted.web.proxy import ProxyRequest


class ProxyClient(proxy.ProxyClient):
    """Mangle returned header, content here.

    Use `self.father` methods to modify request directly.
    """

    def handleHeader(self, key, value):
        # change response header here
        if key == "Access-Control-Allow-Origin":
            value = "*"
        log.msg("Header: %s: %s" % (key, value))
        proxy.ProxyClient.handleHeader(self, key, value)

    def handleResponsePart(self, buffer):
        # change response part here
        log.msg("Content: %s" % (buffer[:50],))
        # make all content upper case
        proxy.ProxyClient.handleResponsePart(self, buffer.upper())


class ProxyClientFactory(proxy.ProxyClientFactory):
    protocol = ProxyClient



class ChangeSomeHeadersProxyRequest(ProxyRequest):
    def process(self):
        self.changeHeaders()
        return ProxyRequest.process(self)

    def changeHeaders(self):
        # Inject an extra request header.
        if not self.requestHeaders.hasHeader(b"access-control-allow-origin"):
            self.requestHeaders.addRawHeader(b"access-control-allow-origin", b"*")


class Proxy(proxy.Proxy):
    requestFactory = ChangeSomeHeadersProxyRequest


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
else:  # $ twistd -ny proxy_modify_request.py
    from twisted.application import service, strports

    application = service.Application("proxy_modify_request")
    strports.service(portstr, ProxyFactory()).setServiceParent(application)

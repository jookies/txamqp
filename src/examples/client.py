#!/usr/bin/env python

# based on the 'calculator' demo in the Thrift source

import sys, os.path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.split(sys.argv[0])[0]), 'gen-py'))
import tutorial.Calculator
from tutorial.ttypes import *
from thrift.transport import TTwisted
from thrift.protocol import TBinaryProtocol

from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator

import txamqp.spec
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.contrib.thrift import TwistedAMQPTransport

servicesExchange = "services"
responsesExchange = "responses"
calculatorQueue = "calculator_pool"
calculatorKey = "calculator"

def gotPing(_):
    print "Ping received"

def gotAddResults(results):
    print "Got results to add()"
    print results

def gotCalculateResults(results):
    print "Got results to calculate()"
    print results

def gotCalculateErrors(error):
    print "Got an error"
    print error.value.why

def gotClient(txclient):
    client = txclient.client
    
    d1 = client.ping().addCallback(gotPing)

    d2 = client.add(1, 2).addCallback(gotAddResults)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.ADD})

    d3 = client.calculate(1, w).addCallbacks(gotCalculateResults, gotCalculateErrors)
    
    w = Work({'num1': 2, 'num2': 3, 'op': Operation.SUBTRACT})
    
    d4 = client.calculate(2, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.MULTIPLY})
    
    d5 = client.calculate(3, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.DIVIDE})
    
    d6 = client.calculate(4, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    # This will fire an errback
    w = Work({'num1': 2, 'num2': 0, 'op': Operation.DIVIDE})
    
    d7 = client.calculate(5, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    d8 = client.zip()

    dl = defer.DeferredList([d1, d2, d3, d4, d5, d6, d7, d8])

    dl.addCallback(lambda _: reactor.stop())

def parseClientMessage(msg, channel, queue, pfactory, thriftClient):
    deliveryTag = msg.delivery_tag
    tr = TTransport.TMemoryBuffer(msg.content.body)
    iprot = pfactory.getProtocol(tr)
    (fname, mtype, rseqid) = iprot.readMessageBegin()

    m = getattr(thriftClient, 'recv_' + fname)
    m(iprot, mtype, rseqid)

    channel.basic_ack(deliveryTag, True)
    queue.get().addCallback(parseClientMessage, channel, queue, pfactory, thriftClient)

@defer.inlineCallbacks
def prepareClient(client, authentication):
    yield client.start(authentication)

    channel = yield client.channel(1)

    yield channel.channel_open()
    yield channel.exchange_declare(exchange=servicesExchange, type="direct")
    yield channel.exchange_declare(exchange=responsesExchange, type="direct")

    reply = yield channel.queue_declare(exclusive=True, auto_delete=True)

    responseQueue = reply.queue

    yield channel.queue_bind(queue=responseQueue, exchange=responsesExchange,
        routing_key=responseQueue)

    amqpTransport = TwistedAMQPTransport(channel, servicesExchange, calculatorKey,
        replyTo=responseQueue, replyToField=replyToField)
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    thriftClient = tutorial.Calculator.Client(amqpTransport, pfactory)

    reply = yield channel.basic_consume(queue=responseQueue)
    queue = yield client.queue(reply.consumer_tag)
    queue.get().addCallback(parseClientMessage, channel, queue, pfactory, thriftClient)
    defer.returnValue(thriftClient)

def gotClient(client):
    d1 = client.ping().addCallback(gotPing)

    d2 = client.add(1, 2).addCallback(gotAddResults)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.ADD})

    d3 = client.calculate(1, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.SUBTRACT})

    d4 = client.calculate(2, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.MULTIPLY})

    d5 = client.calculate(3, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    w = Work({'num1': 2, 'num2': 3, 'op': Operation.DIVIDE})

    d6 = client.calculate(4, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    # This will fire an errback
    w = Work({'num1': 2, 'num2': 0, 'op': Operation.DIVIDE})

    d7 = client.calculate(5, w).addCallbacks(gotCalculateResults, gotCalculateErrors)

    d8 = client.zip()

    dl = defer.DeferredList([d1, d2, d3, d4, d5, d6, d7, d8])

    dl.addCallback(lambda _: reactor.stop())

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 7:
        print "%s host port vhost username password path_to_spec" % sys.argv[0]
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    vhost = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]
    specFile = sys.argv[6]

    spec = txamqp.spec.load(specFile)

    delegate = TwistedDelegate()

    d = ClientCreator(reactor, AMQClient, delegate, vhost,
        spec).connectTCP(host, port)

    if (spec.major, spec.minor) == (8, 0):
        authentication = {"LOGIN": username, "PASSWORD": password}
        replyToField = "reply to"
    else:
        authentication = "\0" + username + "\0" + password
        replyToField = "reply-to"

    d.addCallback(prepareClient, authentication).addCallback(gotClient)
    reactor.run()
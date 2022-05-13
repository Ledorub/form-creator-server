import json

import requests


class JSONRPCError(Exception):
    code = -32603
    msg = 'Internal JSON-RPC error.'

    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        return f'{self.code} - {self.msg}'


class JSONRPCInvalidRequestError(JSONRPCError):
    code = -32600
    msg = 'The JSON sent is not a valid Request object.'


class JSONRPCInvalidParamsError(JSONRPCInvalidRequestError):
    code = -32602
    msg = 'Invalid method parameter(s).'


class JSONRPCMethodError(JSONRPCError):
    code = -32601
    msg = 'The method does not exist / is not available.'


class RPCMessage:
    """
    Generic JSON RPC payload representation.
    """
    _keys = tuple()

    def __init__(self, **kwargs):
        jsonrpc = kwargs.get('jsonrpc', None)
        if not jsonrpc or jsonrpc != '2.0':
            raise JSONRPCInvalidRequestError()
        self.jsonrpc = jsonrpc

    def as_dict(self):
        result = {}
        for k in self._keys:
            if hasattr(self, k):
                result[k] = getattr(self, k)
        return result


class RPCRequest(RPCMessage):
    """
    Representation of an JSON RPC request.
    """
    _keys = ('jsonrpc', 'id', 'method', 'params')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        method = kwargs.get('method', None)
        if not method:
            raise JSONRPCInvalidRequestError('Method is required.')
        self.method = method

        params = kwargs.get('params', None)
        if params:
            self.params = params

        _id = kwargs.get('id', None)
        if _id:
            self.id = _id

    def prepare_response(self, **kwargs):
        """
        Wraps response data into JSON RPC message with the same id as a request.
        """
        if not self.id:
            raise JSONRPCError('Can\'t respond to notification.')
        return RPCResponse(jsonrpc=self.jsonrpc, id=self.id, **kwargs)


class RPCResponse(RPCMessage):
    """
    Representation of an JSON RPC response.
    """
    _keys = ('jsonrpc', 'id', 'result', 'error')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        _id = kwargs.get('id', None)
        if not _id:
            raise JSONRPCError('id is required.')
        self.id = _id

        result = kwargs.get('result', None)
        error = kwargs.get('error', None)
        if not (result or error):
            raise JSONRPCError('result or error is required.')
        elif error:
            self.error = error
        elif result:
            self.result = result


class JSONRPCClient:
    """
    Simple JSON RPC wrapper to call remote procedures.
    """
    JSON_RPC_VERSION = '2.0'
    request_id = 0

    def __init__(self, url):
        self.url = url

    def call(self, method, params):
        request = RPCRequest(
            jsonrpc=self.JSON_RPC_VERSION,
            id=str(self.request_id),
            method=method,
            params=params
        )
        response = requests.post(
                self.url,
                json=request.as_dict()
            )
        self.request_id += 1
        return RPCResponse(**response.json())


class Dispatcher:
    """
    Chooses appropriate RPC method and handles errors during method call.
    """
    _methods = {}

    def register(self, f, name):
        self._methods[name] = f

    def dispatch(self, request):
        method = self._methods.get(request.method, None)
        if not method:
            raise JSONRPCMethodError()

        params = request.params
        result = self._call(method, params)
        return result

    def _call(self, method, params):
        try:
            if not params:
                result = method()
            elif isinstance(params, list):
                result = method(*params)
            else:
                result = method(**params)
        except Exception as error:
            return {'error': self._handle_exception(error)}
        else:
            return {'result': result}

    def _handle_exception(self, error):
        return {
            'code': JSONRPCInvalidParamsError.code,
            'message': str(error)
        }

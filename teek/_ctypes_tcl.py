import contextlib
import ctypes.util
import faulthandler
import sys
import traceback


faulthandler.enable()


class TclError(Exception):
    pass


@ctypes.POINTER
class Tcl_Interp(ctypes.Structure):
    _fields_ = []


@ctypes.POINTER
class Tcl_Obj(ctypes.Structure):
    # refCount is the first field, and we don't need the other fields
    _fields_ = [('refCount', ctypes.c_int)]


@ctypes.POINTER
class Tcl_Command(ctypes.Structure):
    _fields_ = []


TCL_OK = 0
TCL_ERROR = 1


# Tcl's ClientData is a typedef for void* (or int* on systems without void*)
Tcl_CmdProc = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, Tcl_Interp,
    ctypes.c_int, ctypes.POINTER(ctypes.c_char_p))
Tcl_CmdDeleteProc = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

libtcl = ctypes.CDLL(ctypes.util.find_library('tcl8.6'))
libtk = ctypes.CDLL(ctypes.util.find_library('tk8.6'))

# TODO: use Tcl_EvalEx and Tcl_GetStringFromObj
#       the strings could contain \0 bytes
libtcl.Tcl_CreateCommand.argtypes = [Tcl_Interp, ctypes.c_char_p, Tcl_CmdProc,
                                     ctypes.c_void_p, Tcl_CmdDeleteProc]
libtcl.Tcl_CreateCommand.restype = Tcl_Command
libtcl.Tcl_CreateInterp.argtypes = []
libtcl.Tcl_CreateInterp.restype = Tcl_Interp
#libtcl.Tcl_DecrRefCount.argtypes = [Tcl_Obj]
#libtcl.Tcl_DecrRefCount.restype = None
libtcl.Tcl_DeleteCommand.argtypes = [Tcl_Interp, ctypes.c_char_p]
libtcl.Tcl_DeleteCommand.restype = ctypes.c_int
libtcl.Tcl_DeleteInterp.argtypes = [Tcl_Interp]
libtcl.Tcl_DeleteInterp.restype = None
libtcl.Tcl_DoOneEvent.argtypes = [ctypes.c_int]
libtcl.Tcl_DoOneEvent.restype = ctypes.c_int
libtcl.Tcl_Eval.argtypes = [Tcl_Interp, ctypes.c_char_p]
libtcl.Tcl_Eval.restype = ctypes.c_int
libtcl.Tcl_EvalObjv.argtypes = [Tcl_Interp, ctypes.c_int,
                                ctypes.POINTER(Tcl_Obj), ctypes.c_int]
libtcl.Tcl_EvalObjv.restype = ctypes.c_int
libtcl.Tcl_FindExecutable.argtypes = [ctypes.c_char_p]
libtcl.Tcl_FindExecutable.restype = None
libtcl.Tcl_GetBoolean.argtypes = [Tcl_Interp, ctypes.c_char_p,
                                  ctypes.POINTER(ctypes.c_int)]
libtcl.Tcl_GetBoolean.restype = ctypes.c_int
libtcl.Tcl_GetObjResult.argtypes = [Tcl_Interp]
libtcl.Tcl_GetObjResult.restype = Tcl_Obj
libtcl.Tcl_GetString.argtypes = [Tcl_Obj]
libtcl.Tcl_GetString.restype = ctypes.c_char_p
libtcl.Tcl_GetVar.argtypes = [Tcl_Interp, ctypes.c_char_p, ctypes.c_int]
libtcl.Tcl_GetVar.restype = ctypes.c_char_p
#libtcl.Tcl_IncrRefCount.argtypes = [Tcl_Obj]
#libtcl.Tcl_IncrRefCount.restype = None
libtcl.Tcl_Init.argtypes = [Tcl_Interp]
libtcl.Tcl_Init.restype = ctypes.c_int
libtcl.Tcl_InterpDeleted.argtypes = [Tcl_Interp]
libtcl.Tcl_InterpDeleted.restype = ctypes.c_int
libtcl.Tcl_ListObjGetElements.argtypes = [
    Tcl_Interp, Tcl_Obj, ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.POINTER(Tcl_Obj))]
libtcl.Tcl_ListObjGetElements.restype = ctypes.c_int
libtcl.Tcl_NewListObj.argtypes = [ctypes.c_int, ctypes.POINTER(Tcl_Obj)]
libtcl.Tcl_NewListObj.restype = Tcl_Obj
libtcl.Tcl_NewStringObj.argtypes = [ctypes.c_char_p, ctypes.c_int]
libtcl.Tcl_NewStringObj.restype = Tcl_Obj
libtcl.Tcl_Preserve.argtypes = [ctypes.c_void_p]
libtcl.Tcl_Preserve.restype = None
libtcl.Tcl_Release.argtypes = [ctypes.c_void_p]
libtcl.Tcl_Release.restype = None
libtcl.Tcl_SetObjResult.argtypes = [Tcl_Interp, Tcl_Obj]
libtcl.Tcl_SetObjResult.restype = None

libtcl.TclFreeObj.argtypes = [Tcl_Obj]
libtcl.TclFreeObj.restype = None

libtk.Tk_Init.argtypes = [Tcl_Interp]
libtk.Tk_Init.restype = ctypes.c_int


# incref and decref are based on macros in tcl.h
def incref(obj):
    obj.contents.refCount += 1


def decref(obj):
    old = obj.contents.refCount
    obj.contents.refCount -= 1
    if old <= 1:
        libtcl.TclFreeObj(obj)


def _obj_to_string(obj):
    return libtcl.Tcl_GetString(obj).decode('utf-8')


libtcl.Tcl_FindExecutable(sys.executable.encode('utf-8'))


@contextlib.contextmanager
def _with_all(context_managers):
    context_managers = list(context_managers)   # need to loop over this twice

    value = [cm.__enter__() for cm in context_managers]
    try:
        yield value
    finally:
        for cm in context_managers:
            # TODO: should put error here?
            cm.__exit__(None, None, None)


# TODO: use the Tcl_Obj thing instead of the char* thing for callbacks
@Tcl_CmdProc
def callback_runner(client_data, interp, argc, argv):
    try:
        py_obj_ptr = ctypes.cast(client_data, ctypes.POINTER(ctypes.py_object))
        func, name, tkapp = py_obj_ptr.contents.value
        result = func(*([argv[i].decode('utf-8') for i in range(1, argc)]))
        with tkapp._create_string_obj(result) as obj:
            libtcl.Tcl_SetObjResult(tkapp._interp, obj)
        return TCL_OK
    except Exception:
        traceback.print_exc()
        return TCL_ERROR


@Tcl_CmdDeleteProc
def callback_deleter(client_data):
    py_obj_ptr = ctypes.cast(client_data, ctypes.POINTER(ctypes.py_object))
    func, name, tkapp = py_obj_ptr.contents.value
    del tkapp._dont_gc_the_callbacks[name]


class TkApp:

    def __init__(self):
        self._interp = libtcl.Tcl_CreateInterp()
        if not self._interp:
            raise RuntimeError("Tcl_CreateInterp() failed")
        if libtcl.Tcl_Init(self._interp) != TCL_OK:
            raise TclError(self._get_result())
        if libtk.Tk_Init(self._interp) != TCL_OK:
            raise TclError(self._get_result())

        self._exiting_var_name = 'exit_var_%x' % id(self)

        self.eval('rename exit {}')
        self.eval('set %s false' % self._exiting_var_name)
        self.eval('package require Tk')
        self.eval('bind . <Destroy> { set %s true }' % self._exiting_var_name)

        # putting stuff here prevents garbage collection, funny workaround hehe
        self._dont_gc_the_callbacks = {}

    def _get_result(self):
        result = libtcl.Tcl_GetObjResult(self._interp)
        if not result:
            raise TclError("Tcl_GetObjResult() returned NULL")
        return _obj_to_string(result)

    def eval(self, code):
        if libtcl.Tcl_Eval(self._interp, code.encode('utf-8')) != TCL_OK:
            raise TclError(self._get_result())
        return self._get_result()

    @contextlib.contextmanager
    def _create_string_obj(self, python_str_or_tuple):
        if isinstance(python_str_or_tuple, str):
            bytez = python_str_or_tuple.encode('utf-8')
            obj = libtcl.Tcl_NewStringObj(bytez, len(bytez))
        elif isinstance(python_str_or_tuple, tuple):
            with _with_all(map(self._create_string_obj,
                               python_str_or_tuple)) as item_objects:
                objv = (Tcl_Obj * len(item_objects))()
                for index, obj in enumerate(item_objects):
                    objv[index] = obj
                obj = libtcl.Tcl_NewListObj(len(item_objects), objv)
        else:
            raise TypeError("expected str or tuple, got " +
                            repr(python_str_or_tuple))
        if not obj:
            raise TclError(self._get_result())

        # tcl initializes the refcount to 0 for some reason
        incref(obj)
        try:
            yield obj
        finally:
            decref(obj)

    def call(self, *args, asdf=False):
        with _with_all(map(self._create_string_obj, args)) as arg_objects:
            objv = (Tcl_Obj * len(arg_objects))()
            for index, obj in enumerate(arg_objects):
                objv[index] = obj

            if libtcl.Tcl_EvalObjv(self._interp, len(objv), objv, 0) != TCL_OK:
                raise TclError(self._get_result())
            return self._get_result()

    def createcommand(self, name, func):
        assert name not in self._dont_gc_the_callbacks

        data = (func, name, self)
        void_pointer = ctypes.cast(ctypes.pointer(ctypes.py_object(data)),
                                   ctypes.c_void_p)
        result = libtcl.Tcl_CreateCommand(self._interp, name.encode('utf-8'),
                                          callback_runner, void_pointer,
                                          callback_deleter)
        if not result:
            raise TclError(self._get_result())
        self._dont_gc_the_callbacks[name] = (func, void_pointer)

    def deletecommand(self, name):
        if libtcl.Tcl_DeleteCommand(self._interp, name.encode('utf-8')) < 0:
            raise TclError("command not found: " + name)

    def splitlist(self, string):
        with self._create_string_obj(string) as list_obj:
            objc_ptr = (ctypes.c_int * 1)()
            objv_ptr = (ctypes.POINTER(Tcl_Obj) * 1)()

            status = libtcl.Tcl_ListObjGetElements(
                self._interp, list_obj, objc_ptr, objv_ptr)
            if status != TCL_OK:
                raise TclError(self._get_result())

            result_objects = (objv_ptr[0][i] for i in range(objc_ptr[0]))
            return list(map(_obj_to_string, result_objects))

    def getboolean(self, string):
        bool_ptr_which_is_int_array = (ctypes.c_int * 1)()
        if libtcl.Tcl_GetBoolean(self._interp, string.encode('utf-8'),
                                 bool_ptr_which_is_int_array) == TCL_OK:
            return bool(bool_ptr_which_is_int_array[0])
        raise TclError(self._get_result())

    def mainloop(self, junk):
        while True:
            libtcl.Tcl_DoOneEvent(0)
            exiting_var = self._exiting_var_name.encode('ascii')
            if libtcl.Tcl_InterpDeleted(self._interp):
                break
            if libtcl.Tcl_GetVar(self._interp, exiting_var, 0) == b'true':
                break

    def delete(self):
        libtcl.Tcl_DeleteInterp(self._interp)


def create(*junk):
    return TkApp()


if __name__ == '__main__':
    app = create()
    app.call('puts', 'hello world')
    print(app.splitlist('a b {c and d}'))
    print(app.call('list', 'a', 'b', 'c and d'))

    app.createcommand('tcl_print', lambda x: print(x, end='!\n'))
    app.eval('tcl_print lollöl')
    app.eval('tcl_print lol')
    app.eval('tcl_print lol')
    app.eval('tcl_print lol')
    app.deletecommand('tcl_print')

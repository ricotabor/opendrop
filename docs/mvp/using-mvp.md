Opendrop MVP Framework
======================

This document will outline the usage of the internal MVP framework.

There are five main components of the framework:
 - `Model`
 - `Presenter`
 - `View`
 - `IView`
 - `Application`

Broad Overview
--------------

`Model` is used to store and retrieve data, and give the `Presenter`
access to other services of the program unrelated to the user interface.

`Presenter` handles user input and transforms them to an appropriate
data format to be used with the services in `Model`. It then takes the
output of from `Model` and sends it to the `View` for presentation.

`View` is responsible for the displaying of information and
forwarding user input to the `Presenter`. It does this by exposing
methods and events that the `Presenter` can call and connect to.

`IView` is the `View`'s interface that the `Presenter` has a
dependency with. It specifies the methods and attributes that the `View`
should implement.

`Application` manages the lifecycle of `View`s and `Presenter`s, as well
as the wiring of dependencies for both objects

**More Details:**

Each `Presenter` has a reference to one `Model` and one `View`, neither
`Model` nor `View` has a reference to the `Presenter`.

The `Model`, `IView`, and `Presenter` classes should be independent to
the GUI library used for the user interface, code for this should be
in the `View`.

View/Presenter Lifecycle
------------------------

In a `View`/`Presenter` pair, the `View` is first initialised, followed
by the `Presenter`, passing in the `Model` object and `View` object as
arguments. The `Model` object is created at the start of the application
and is shared among all the `Presenter` objects.

When a `Presenter` and `View` is first created, their `setup()` methods
are called. Since `View`s are the first to be initialised,
`Presenter.setup()` is always called after `View.setup()`.

When a `View` is destroyed, its `teardown()` method is called. Its
`Presenter` is then destroyed and its `teardown()` method is
subsequently called as well.

The `Presenter` is never destroyed directly, the `View` is always the
object that is destroyed. `Presenter` has a handler that connects to the
`View`'s destroy event, the handler will call the appropriate destroy
method on the `Presenter` whenever the `View` is destroyed.

How to use
----------

The `Application`, `Model`, `View`, and `Presenter` classes are intended
to be subclassed. As the `Application` and `View` classes do not provide
any implementation or GUI libraries, they should be subclassed into
`GtkApplication` and `GtkView` for example, and your actual
implementations should further subclass those (see the sample
application).

Subclassing `Presenter` is as follows:

    MyPresenter(Presenter[MyModel, IMyView]):
        pass

Where `MyModel` is an implementation of `Model` and `IMyView` is the
interface for the view that `MyPresenter` presents.

Subclassing `Application`:

    SampleApplication(Application):
        MODEL = MyModel
        VIEWS = [MyView, OtherView, CoolView]
        PRESENTERS = [MyPresenter, OtherPresenter, CoolPresenter]

        ENTRY_VIEW = MyView

`MODEL` specifies the `Model` class object that will be used by the
application's presenters.

`VIEWS` specifies the list of views your application contains.

`PRESENTERS` likewise specifies the list of presenters that your
application uses.

`ENTRY_VIEW` is the first view that the application begins in.

In your application, each presenter may be capable of presenting more
than one view, but each view must have only one presenter that can
present it, otherwise the behaviour is undefined.

The method that `Application` uses to pair up each `View` to its
corresponding `Presenter` is by going through the `PRESENTERS` list and
checking `Presenter.can_present(View)`, if this returns `True` then the
presenter is selected.

Examples
--------
See provided sample application.
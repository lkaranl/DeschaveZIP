#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import sys

from deschavezip.dependency_checker import check_dependencies, show_dependency_error

# Verifica dependências antes de tentar importar GTK
if not check_dependencies():
    show_dependency_error()
    sys.exit(1)

gi.require_version('Gtk', '4.0')
try:
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, GLib, Gio, Adw
    HAS_ADW = True
except (ValueError, ImportError):
    from gi.repository import Gtk, GLib, Gio
    HAS_ADW = False

from deschavezip.ui.app_window import AppWindow

class DeschaveZIPApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.deschavezip",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = AppWindow(application=self)
        win.present()

def main():
    # Configurar o tema escuro se disponível
    settings = Gtk.Settings.get_default()
    if settings is not None:
        settings.set_property("gtk-application-prefer-dark-theme", True)
    
    if HAS_ADW:
        # Use o estilo Adwaita se disponível
        app = Adw.Application(application_id="com.github.deschavezip",
                              flags=Gio.ApplicationFlags.FLAGS_NONE)
        app.connect("activate", on_activate_adw)
    else:
        app = DeschaveZIPApp()
    
    return app.run(None)

def on_activate_adw(app):
    win = app.get_active_window()
    if not win:
        win = AppWindow(application=app)
    win.present()

if __name__ == "__main__":
    main() 
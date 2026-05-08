"""Launcher shim — runs the lights_off package."""
import runpy
runpy.run_module("lights_off", run_name="__main__", alter_sys=True)

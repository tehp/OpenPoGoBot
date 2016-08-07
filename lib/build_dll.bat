@echo off
cl encrypt.c /link /dll /out:encrypt.dll /export:encrypt

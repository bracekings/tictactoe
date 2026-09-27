import sys
print('executable:', sys.executable)
print('version:', sys.version)
print('\nfirst 6 sys.path entries:')
for p in sys.path[:6]:
    print('  ', p)
try:
    import pygame
    v = getattr(pygame, 'version', None)
    print('pygame import succeeded, version attr:', getattr(v, 'ver', v))
except Exception as e:
    import traceback
    print('pygame import failed:')
    traceback.print_exc()

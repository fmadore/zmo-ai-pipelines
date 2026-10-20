"""Compatibility entry point: all modules now use the shared notebook builder."""

from build_notebooks import build

if __name__ == '__main__':
    build()

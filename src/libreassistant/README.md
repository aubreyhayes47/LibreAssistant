# LibreAssistant Core

This package contains the runtime pieces that power the LibreAssistant API server.

## Kernel

The [kernel](./kernel.py) implements a tiny microkernel that keeps per-user state and routes
requests to registered plugins.

## Plugins

Built-in plugins live in the [plugins](./plugins/) directory.  Each plugin exposes a
`register()` helper that adds the plugin to the kernel during start-up.

## Providers

Language model backends are wrapped by the [providers](./providers/) registry.  The
`ProviderManager` securely stores API keys and dispatches prompts to either local or cloud
implementations.

## Entrypoints

- [main.py](./main.py) builds the FastAPI application, registers default plugins and providers,
  and exposes REST endpoints.
- [__main__.py](./__main__.py) runs the application with Uvicorn for local development.

## Additional Resources

- [Documentation](../../docs/)
- [Experts](./experts/)
- [Plugins](./plugins/)
- [Providers](./providers/)

1. General:
   1. The package must be functional on the [latest version of Meson](https://github.com/mesonbuild/meson/releases/latest).
   2. The package must contain safe content.
2. Naming:
   1. The package name must contain only lowercase Latin characters (`a-z`), digits (`0-9`) and the `-` character. (`^[a-z0-9-]+$`)
   2. The package version must fully follow the [scheme](https://packaging.python.org/en/latest/specifications/version-specifiers/#public-version-identifiers).
   3. The provision name must match the package name or begin with it, separated from the main part by the `-` character. The main part must contain only lowercase Latin characters (`a-z`), digits (`0-9`) and the `-` character. (`^{package_name}$|^{package_name}-[a-z0-9-]+$`)
3. Configuration:
   1. Only `wrap-file` type is allowed.
   2. The header section must contain the `wrapdb_version` parameter, which indicates the version of the package.
   3. The following parameters are not allowed to be used in the header section:
      - `patch_url`
      - `patch_hash`
      - `patch_filename`
      - `patch_fallback_url`
      - `source_fallback_url`

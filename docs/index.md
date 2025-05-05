:::{image} _static/logo.svg
:class: only-light
:alt: Chexus
:width: 60%
:align: center
:::
:::{image} _static/logo-dark.svg
:class: only-dark
:alt: Chexus
:width: 60%
:align: center
:::

```{raw} html
   <style>
    .transparent {display: none; visibility: hidden;}
    .transparent + a.headerlink {display: none; visibility: hidden;}
   </style>
```

```{role} transparent
```

# {transparent}`Chexus`

<span style="font-size:1.2em;font-style:italic;color:var(--pst-color-text-muted);text-align:center;">
  Validate and check NeXus files
  </br></br>
</span>

## Installation

To install Chexus and all of its dependencies, use

`````{tab-set}
````{tab-item} pip
```sh
pip install chexus
```
````
````{tab-item} conda
```sh
conda install -c conda-forge -c scipp chexus
```
````
`````

## Run

```bash
chexus <path-to-nexus-file>
```

This supports HDF5 as well as some JSON format.
There is also a Python API, but this is under construction and unstable.

## Options

- `--checksums`: Compute and print checksums.
- `--ignore-missing`: Skip the validators that have missing dependencies.
- `--exit-on-fail`: Return a non-zero exit code if validation fails.
- `-r`, `--root-path`: Path to the top-level group to validate. Default is `''`.

## Get in touch

- If you have questions that are not answered by these documentation pages, ask on [discussions](https://github.com/scipp/chexus/discussions). Please include a self-contained reproducible example if possible.
- Report bugs (including unclear, missing, or wrong documentation!), suggest features or view the source code [on GitHub](https://github.com/scipp/chexus).

```{toctree}
---
hidden:
---

api-reference/index
developer/index
about/index
```

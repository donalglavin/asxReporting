{pkgs ? import <nixpkgs> {}}: let
  my-python = pkgs.python3.withPackages (p:
    with p; [
      pandas
      matplotlib
      requests
      plotly
      yfinance
      jinja2 # Required by Pandas for the DataFrame.style.to_html() method
    ]);
in
  pkgs.mkShell {
    buildInputs = [
      my-python
    ];

    shellHook = ''
      echo "ASX Data & Plotly environment loaded!"
      python --version
    '';
  }

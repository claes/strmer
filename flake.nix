{
  description = "Regelverk";

  # Nixpkgs / NixOS version to use.
  inputs.nixpkgs.url = "nixpkgs/nixos-24.11";

  outputs = {
    self,
    nixpkgs,
  }: let
    # to work with older version of flakes
    lastModifiedDate = self.lastModifiedDate or self.lastModified or "19700101";

    # Generate a user-friendly version number.
    version = builtins.substring 0 8 lastModifiedDate;

    # System types to support.
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin"];

    # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

    # Nixpkgs instantiated for supported system types.
    nixpkgsFor = forAllSystems (system: import nixpkgs {inherit system;});
  in {
    # Provide some binary packages for selected system types.
    packages = forAllSystems (system: let
      pkgs = nixpkgsFor.${system};

      strmer = pkgs.buildGoModule {
        pname = "strmer";
        inherit version;
        # In 'nix develop', we don't need a copy of the source tree
        # in the Nix store.
        src = ./.;

        # This hash locks the dependencies of this package. It is
        # necessary because of how Go requires network access to resolve
        # VCS.  See https://www.tweag.io/blog/2021-03-04-gomod2nix/ for
        # details. Normally one can build with a fake sha256 and rely on native Go
        # mechanisms to tell you what the hash should be or determine what
        # it should be "out-of-band" with other tooling (eg. gomod2nix).
        # To begin with it is recommended to set this, but one must
        # remeber to bump this hash when your dependencies change.
        #vendorSha256 = pkgs.lib.fakeSha256;

        nativeBuildInputs = [];
        buildInputs = [];

        vendorHash = null;

        #Also copy the Kodi Python plugin to the result
        postInstall = ''
          cp -r plugin.video.strmer $out/plugin.video.strmer
        '';
      };
    in {
      strmer = strmer;
    });

    devShells = forAllSystems (system: let
      pkgs = nixpkgsFor.${system};
    in {
      default = pkgs.mkShell {
        buildInputs = [
          pkgs.python3
          pkgs.python310Packages.pip
          pkgs.python310Packages.virtualenv
          pkgs.zip
          pkgs.unzip
          pkgs.git
          pkgs.go
          pkgs.gopls
          pkgs.gotools
          pkgs.go-tools
          pkgs.go-outline
          pkgs.godef
          pkgs.delve
        ];
      };
    });

    # The default package for 'nix build'.
    defaultPackage = forAllSystems (system: self.packages.${system}.strmer);
  };
}

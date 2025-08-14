# replit.nix
{ pkgs }: {
  main = pkgs.mkShell {
    # buildInputs son los paquetes cuyos ejecutables estarán disponibles en el PATH
    buildInputs = with pkgs; [
      # ---- Entorno de Python ----
      python311      # Instala Python 3.11
      poetry         # Una herramienta moderna para gestionar dependencias de Python

      # ---- Entorno de Node.js ----
      nodejs_18      # Instala Node.js v18 (incluye npm)
      
      # ---- Dependencias del Sistema ----
      # Necesarias para que algunas librerías de Python se compilen correctamente
      libxml2
      libxslt
    ];
  };
}
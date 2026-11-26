#!/data/data/com.termux/files/usr/bin/bash
# Instalador do projeto "Natal no Termux"

REPO="https://github.com/daniel810e-hue/natal-termux.git"
PASTA="$HOME/natal-termux"

echo "Instalando Natal no Termux..."

pkg update -y
pkg install git -y

# Se já existe, atualiza. Se não, baixa.
if [ -d "$PASTA" ]; then
  cd "$PASTA" && git pull
else
  git clone "$REPO" "$PASTA"
fi

# Cria o comando "natal" que funciona de qualquer pasta
chmod +x "$PASTA/natal.sh"
ln -sf "$PASTA/natal.sh" "$PREFIX/bin/natal"

echo ""
echo "Pronto! Agora digite: natal"
natal

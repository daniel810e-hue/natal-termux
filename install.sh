#!/data/data/com.termux/files/usr/bin/bash

# ===== MUDE SÓ ESTAS 5 LINHAS =====
USUARIO="daniel810e-hue"
REPO="nome-do-repositorio"
COMANDO="nome-do-comando"
ARQUIVO="gamkers_monitor.py"
DEPENDENCIAS="requests flask"
# ==================================

PASTA="$HOME/$REPO"

pkg update -y
pkg install python git -y
[ -n "$DEPENDENCIAS" ] && pip install $DEPENDENCIAS

if [ -d "$PASTA" ]; then
  cd "$PASTA" && git pull
else
  git clone "https://github.com/$USUARIO/$REPO.git" "$PASTA"
fi

echo '#!/data/data/com.termux/files/usr/bin/bash' > "$PREFIX/bin/$COMANDO"
echo "cd $PASTA" >> "$PREFIX/bin/$COMANDO"
echo "python $ARQUIVO" >> "$PREFIX/bin/$COMANDO"
chmod +x "$PREFIX/bin/$COMANDO"

echo "Pronto! Digite: $COMANDO"
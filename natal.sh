#!/data/data/com.termux/files/usr/bin/bash
# Programa principal: mensagem de boas-vindas de dezembro

VERDE='\033[1;32m'
VERMELHO='\033[1;31m'
AMARELO='\033[1;33m'
FIM='\033[0m'

clear
echo -e "${VERDE}"
echo "        *"
echo "       /o\\"
echo "      /o o\\"
echo "     /o o o\\"
echo "    /o o o o\\"
echo "   /o o o o o\\"
echo "        |"
echo -e "${FIM}"
echo -e "${VERMELHO}  Seja bem-vindo ao Natal no Termux!${FIM}"
echo ""

# Contagem regressiva até 25 de dezembro
ANO=$(date +%Y)
HOJE=$(date +%s)
NATAL=$(date -d "$ANO-12-25" +%s)

if [ "$HOJE" -gt "$NATAL" ]; then
  ANO=$((ANO + 1))
  NATAL=$(date -d "$ANO-12-25" +%s)
fi

DIAS=$(( (NATAL - HOJE) / 86400 ))

if [ "$DIAS" -eq 0 ]; then
  echo -e "${AMARELO}  Hoje é Natal! Feliz Natal!${FIM}"
else
  echo -e "${AMARELO}  Faltam $DIAS dias para o Natal.${FIM}"
fi

echo ""
echo "  Feito com Termux. Boas festas!"
echo ""

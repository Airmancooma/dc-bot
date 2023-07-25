# Létrehozunk egy új fájlt, pl. 'install.sh', a szükséges csomagok telepítésére
echo "#!/bin/bash" > install.sh

# Frissítjük a rendszert
echo "sudo apt update -y" >> install.sh
echo "sudo apt upgrade -y" >> install.sh

# Telepítjük a Node.js-t
echo "sudo apt install nodejs -y" >> install.sh

# Telepítjük az NPM-t (Node Package Manager)
echo "sudo apt install npm -y" >> install.sh

# Telepítjük a Discord.js csomagot
echo "npm install discord.js" >> install.sh

# Telepítjük a szükséges kriptográfiai csomagokat
echo "npm install tweetnacl" >> install.sh
echo "npm install sodium" >> install.sh
echo "npm install libsodium-wrappers" >> install.sh

# Adjuk hozzá a futtatási jogot a 'install.sh' fájlhoz
chmod +x install.sh

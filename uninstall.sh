printf "It's recommended you run these steps manually.\n"
printf "If you want to run the full script, open it in\n"
printf "an editor and remove 'exit 1' from below.\n"
exit 1
source /home/emshort/.virtualenvs/pimoroni/bin/activate
python -m pip uninstall inky
cp /home/emshort/Pimoroni/config-backups/config.preinstall-inky-2025-12-31-13-34-38.txt /boot/firmware/config.txt
rm -r /home/emshort/Pimoroni/inky

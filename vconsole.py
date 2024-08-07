import subprocess
import shlex
import json
import logging
import os
from typing import Optional
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class MachineConfig:
    name: str
    host: str
    user: str
    password: str
    title: Optional[str]


@dataclass
class VConsoleConfig:
    jre_path: str


class VConsole:
    vconsole_config: VConsoleConfig
    machine_config: list[MachineConfig]

    @classmethod
    def init(cls):
        config_path = "./config.json"
        if not os.path.exists(config_path):
            logging.warning(
                "Configuration file not found. Creating a default configuration file."
            )
            cls.create_default_config()
        else:
            try:
                with open(config_path, mode="r") as fp:
                    json_data = json.load(fp)
                    cls.vconsole_config = VConsoleConfig(**json_data["vconsole_config"])
                    cls.machine_config = [
                        MachineConfig(**config)
                        for config in json_data["machine_config"]
                    ]
                    logging.info("Configuration loaded successfully.")
            except json.JSONDecodeError:
                logging.error("Error decoding JSON from the configuration file.")

    @classmethod
    async def start_console(cls, name: str):
        machine = next((m for m in cls.machine_config if m.name == name), None)
        if not machine:
            logging.error(f"No machine found with name {name}")
            return
        command_str = (
            f"{cls.vconsole_config.jre_path} -cp avctKVM.jar -Djava.library.path=./lib -Duser.language=zh "
            f"com.avocent.idrac.kvm.Main ip={machine.host} vm=1 title={machine.title} user={machine.user} "
            f"passwd={machine.password} kmport=5900 vport=5900 apcp=1 reconnect=2 chat=1 F1=0 custom=0 "
            f"scaling=15 minwinheight=100 minwinwidth=100 videoborder=0 version=2"
        )
        subprocess.run(shlex.split(command_str))

    @classmethod
    async def add_machine(
        cls, name: str, host: str, user: str, password: str, title: Optional[str] = None
    ):
        new_machine = MachineConfig(
            name=name, host=host, user=user, password=password, title=title
        )
        cls.machine_config.append(new_machine)
        cls.save_config()

    @classmethod
    async def remove_machine(cls, name: str):
        machine = next((m for m in cls.machine_config if m.name == name), None)
        if machine:
            cls.machine_config.remove(machine)
            cls.save_config()
            logging.info(f"Machine {name} removed successfully.")
        else:
            logging.error(f"No machine found with name {name}")

    @classmethod
    def save_config(cls):
        with open("./config.json", mode="w") as fp:
            json_data = {
                "vconsole_config": asdict(cls.vconsole_config),
                "machine_config": [asdict(mc) for mc in cls.machine_config],
            }
            json.dump(json_data, fp, indent=4)

    @classmethod
    def create_default_config(cls):
        cls.vconsole_config = VConsoleConfig(jre_path="/path/to/default/jre")
        cls.machine_config = [
            MachineConfig(
                name="DefaultMachine",
                host="127.0.0.1",
                user="admin",
                password="admin",
                title="DefaultTitle",
            )
        ]
        cls.save_config()
        logging.info("Default configuration file created.")

# Load environment variables from .env file
include .env

# Define the default target
.DEFAULT_GOAL := run

# setup venv
setup:
	@echo "Setting up virtual environment..."
	@virtualenv venv
	@echo "Activating virtual environment..."
	@source venv/bin/activate
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@echo "Done!"

# Define the run target
run:
	pulumi up

# Define the update-example-env target
update-example-env:
	@echo "Updating .example.env..."
	@awk -F '=' '{print $$1}' .env > .example.env
	@echo "Done!"

run-urn:
	pulumi up -r \
	-t urn:pulumi:dev::pulumi-proxmox::proxmoxve:VM/virtualMachine:VirtualMachine::vm*

generate_result_yaml:
	@echo "Generating result.yaml..."
	@for file in vms/overlay/*.yaml; do \
		yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' vms/base/base.yaml $$file > vms/result/$$(basename $$file); \
	done
	@echo "Result yaml files generated successfully."


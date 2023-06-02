ansible-inventory -i inventory.yml --graph --vars

ansible-playbook ping.yml -i inventory.yml --limit alma01.1.mgmt.dvag.net
ansible-playbook ping.yml -i inventory.yml --limit alma01.1.mgmt.dvag.net --ask-pass

ansible-playbook show_vm_vars_and_facts.yml -i inventory.yml --limit alma01.1.mgmt.dvag.net
## ansibe inventory

ansible-inventory --graph

ansible-inventory --graph --vars

ansible-inventory --host alma01.salxtest.dvag.net

## debug_play.sh --list-tasks

./debug_play.sh alma01.salxtest.dvag.net --list-tasks

./debug_play.sh alma01.salxtest.dvag.net --list-tasks --tags minimal_server/defender


## ansible-playbook

./debug_play.sh alma01.salxtest.dvag.net --tags top/zob/auth --ask-pass

./ansible_play.sh alma01.salxtest.dvag.net
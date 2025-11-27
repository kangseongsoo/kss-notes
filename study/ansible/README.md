✅ 1단계: Ansible Control Node(node1) 세팅
🔧 (1) 패키지 업데이트 & 툴 설치
dnf update -y
dnf install epel-release -y
dnf install vim git python3 python3-pip -y
🔧 (2) Ansible 설치
dnf install ansible -y
🔑 (3) SSH 키 생성
ssh-keygen
ls ~/.ssh
🔐 (4) SSH 공개키를 node2·node3에 배포
ssh-copy-id root@192.168.219.106
ssh-copy-id root@192.168.219.107

✅ 2단계: Inventory 작성 + Ping 테스트
Inventory 파일 생성
권한/설정 확인
Ansible ping 테스

🔧 (1) Inventory 파일 생성
Ansible 기본 경로는 /etc/ansible/hosts 이지만
프로젝트 폴더를 만들고 관리하는것이 좋다
```
ansible_lab/
 ├── ansible.cfg
 ├── inventory/
 │    └── hosts.ini
 ├── vars/
 │    └── packages.yml
 ├── playbooks/
 │    └── install_packages.yml
 └── roles/
      └── common_packages/
           └── tasks/
                └── main.yml

```
node1에서 실행:
```
mkdir -p /root/ansible_lab
cd /root/ansible_lab
mkdir inventory playbooks roles vars
mkdir -p roles/common_packages/tasks/
```
Inventory 만들기:
```
vi inventory/hosts.ini
[nodes]
192.168.219.106
192.168.219.107

[web]
192.168.219.106

[db]
192.168.219.107

[all:vars]
ansible_user=root
ansible_ssh_private_key_file=/root/.ssh/id_rsa
```
nodes 그룹 이름에 node2, node3 등록
전체 서버는 root 계정 SSH로 접근
SSH 키는 id_rsa 사용(1단계에서 생성한 키)

🔧 (2) Inventory 사용하도록 ansible.cfg 설정
```
vi ansible.cfg
[defaults]
inventory = ./inventory/hosts.ini   # 프로젝트 전용 서버 목록 사용 
host_key_checking=False             # SSH fingerprint 확인 끔 (자동화 필수)
retry_files_enabled=False           # 실패 호스트 기록 파일 생성 금지
roles_path = ./roles
```
🔧 (3) vars/packages.yml
```
---

# 운영 서버용 최소 패키지
base_packages:
  - lsof
  - net-tools
  - sysstat
  - strace
  - htop
  - iotop
  - wget
  - curl
  - mlocate
  - nmap
  - nmap-ncat
  - tcpdump
  - bind-utils
  - traceroute
  - iperf3
  - zip
  - unzip
  - tar
  - bzip2
  - gzip
  - xz
  - p7zip
  - p7zip-plugins
  - vim-enhanced
  - nano
  - tree
  - jq

# DB 서버용 패키지
db_packages:
  - mariadb
  - mariadb-server
  - mariadb-backup

# Apache + Tomcat 웹서버 패키지
web_packages:
  - httpd
  - httpd-tools
  - mod_ssl
  - java-17-openjdk
  - java-17-openjdk-devel
  - tomcat
  - tomcat-admin-webapps
  - tomcat-webapps
```
🔧  (4) roles/common_packages/tasks/main.yml
```
---
- name: Load package variables
  include_vars:
    file: "{{ playbook_dir }}/../vars/packages.yml"

# Web 서버
- name: Install web server packages
  yum:
    name: "{{ web_packages }}"
    state: present
  when: "'web' in group_names"

# DB 서버
- name: Install database server packages
  yum:
    name: "{{ db_packages }}"
    state: present
  when: "'db' in group_names"

# 모든 서버에 공통 설치
- name: Install base packages on all servers
  yum:
    name: "{{ base_packages }}"
    state: present
```
✔ 동작 방식
web 그룹에 속한 서버 → base + web 설치
db 그룹에 속한 서버 → base + db 설치
다른 서버는 base만 설치됨

🔧 (5) playbooks/install_packages.yml — 실행 시나리오(Playbook)
```
---
- hosts: all
  become: yes
  pre_tasks:
    - name: Ensure EPEL repository is enabled
      yum:
        name: epel-release
        state: present

    - name: Refresh DNF/YUM metadata cache
      command: dnf makecache
  roles:
    - common_packages
```

# Role 안에 “설치 검증(verify) 작업”을 추가
✅ 1단계: Role 안에 verify.yml 생성
```
vi roles/common_packages/tasks/verify.yml
```

```
---
# base_packages 설치 검증
- name: Verify base packages installed
  command: "rpm -q {{ item }}"
  register: base_pkg_check
  changed_when: false
  failed_when: base_pkg_check.rc != 0
  loop: "{{ base_packages }}"

- debug:
    msg: "Base package '{{ item.item }}' found: {{ item.stdout }}"
  loop: "{{ base_pkg_check.results }}"

# Web 패키지 검증
- name: Verify web packages installed
  command: "rpm -q {{ item }}"
  register: web_pkg_check
  changed_when: false
  failed_when: "'web' in group_names and web_pkg_check.rc != 0"
  loop: "{{ web_packages }}"
  when: "'web' in group_names"

- debug:
    msg: "Web package '{{ item.item }}' found: {{ item.stdout }}"
  loop: "{{ web_pkg_check.results }}"
  when: "'web' in group_names"

# DB 패키지 검증
- name: Verify db packages installed
  command: "rpm -q {{ item }}"
  register: db_pkg_check
  changed_when: false
  failed_when: "'db' in group_names and db_pkg_check.rc != 0"
  loop: "{{ db_packages }}"
  when: "'db' in group_names"

- debug:
    msg: "DB package '{{ item.item }}' found: {{ item.stdout }}"
  loop: "{{ db_pkg_check.results }}"
  when: "'db' in group_names"
```
🔥 2단계: main.yml 마지막 줄에 include_tasks 추가
roles/common_packages/tasks/main.yml 아래에 마지막에 추가:
```
- include_tasks: verify.yml
```

# 결과
```
[root@node1 ansible_lab]# ansible-playbook playbooks/install_packages.yml

PLAY [all] **********************************************************************************************************************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************************************************************************************************
ok: [192.168.219.107]
ok: [192.168.219.106]

TASK [Ensure EPEL repository is enabled] ****************************************************************************************************************************************************************************************************
ok: [192.168.219.107]
ok: [192.168.219.106]

TASK [Refresh DNF/YUM metadata cache] *******************************************************************************************************************************************************************************************************
changed: [192.168.219.106]
changed: [192.168.219.107]

TASK [common_packages : Load package variables] *********************************************************************************************************************************************************************************************
ok: [192.168.219.106]
ok: [192.168.219.107]

TASK [common_packages : Load package variables] *********************************************************************************************************************************************************************************************
skipping: [192.168.219.107]
ok: [192.168.219.106]

TASK [common_packages : Install database server packages] ***********************************************************************************************************************************************************************************
skipping: [192.168.219.106]
ok: [192.168.219.107]

TASK [common_packages : Install base packages on all servers] *******************************************************************************************************************************************************************************
ok: [192.168.219.107]
ok: [192.168.219.106]

TASK [common_packages : include_tasks] ******************************************************************************************************************************************************************************************************
included: /root/ansible_lab/roles/common_packages/tasks/verify.yml for 192.168.219.106, 192.168.219.107

TASK [common_packages : Verify base packages installed] *************************************************************************************************************************************************************************************
ok: [192.168.219.107] => (item=lsof)
ok: [192.168.219.106] => (item=lsof)
ok: [192.168.219.107] => (item=net-tools)
ok: [192.168.219.106] => (item=net-tools)
ok: [192.168.219.107] => (item=sysstat)
ok: [192.168.219.106] => (item=sysstat)
ok: [192.168.219.107] => (item=strace)
ok: [192.168.219.106] => (item=strace)
ok: [192.168.219.107] => (item=htop)
ok: [192.168.219.106] => (item=htop)
ok: [192.168.219.107] => (item=iotop)
ok: [192.168.219.106] => (item=iotop)
ok: [192.168.219.107] => (item=wget)
ok: [192.168.219.107] => (item=curl)
ok: [192.168.219.106] => (item=wget)
ok: [192.168.219.107] => (item=mlocate)
ok: [192.168.219.106] => (item=curl)
ok: [192.168.219.107] => (item=nmap)
ok: [192.168.219.106] => (item=mlocate)
ok: [192.168.219.107] => (item=nmap-ncat)
ok: [192.168.219.106] => (item=nmap)
ok: [192.168.219.107] => (item=tcpdump)
ok: [192.168.219.106] => (item=nmap-ncat)
ok: [192.168.219.107] => (item=bind-utils)
ok: [192.168.219.107] => (item=traceroute)
ok: [192.168.219.106] => (item=tcpdump)
ok: [192.168.219.107] => (item=iperf3)
ok: [192.168.219.106] => (item=bind-utils)
ok: [192.168.219.107] => (item=zip)
ok: [192.168.219.106] => (item=traceroute)
ok: [192.168.219.107] => (item=unzip)
ok: [192.168.219.106] => (item=iperf3)
ok: [192.168.219.107] => (item=tar)
ok: [192.168.219.106] => (item=zip)
ok: [192.168.219.107] => (item=bzip2)
ok: [192.168.219.106] => (item=unzip)
ok: [192.168.219.107] => (item=gzip)
ok: [192.168.219.107] => (item=xz)
ok: [192.168.219.106] => (item=tar)
ok: [192.168.219.107] => (item=p7zip)
ok: [192.168.219.106] => (item=bzip2)
ok: [192.168.219.107] => (item=p7zip-plugins)
ok: [192.168.219.106] => (item=gzip)
failed: [192.168.219.107] (item=vim) => {"ansible_loop_var": "item", "changed": false, "cmd": ["rpm", "-q", "vim"], "delta": "0:00:00.014755", "end": "2025-11-28 00:00:29.888328", "failed_when_result": true, "item": "vim", "msg": "non-zero return code", "rc": 1, "start": "2025-11-28 00:00:29.873573", "stderr": "", "stderr_lines": [], "stdout": "package vim is not installed", "stdout_lines": ["package vim is not installed"]}
ok: [192.168.219.106] => (item=xz)
ok: [192.168.219.107] => (item=nano)
ok: [192.168.219.106] => (item=p7zip)
ok: [192.168.219.107] => (item=tree)
ok: [192.168.219.107] => (item=jq)
ok: [192.168.219.106] => (item=p7zip-plugins)
failed: [192.168.219.106] (item=vim) => {"ansible_loop_var": "item", "changed": false, "cmd": ["rpm", "-q", "vim"], "delta": "0:00:00.012411", "end": "2025-11-28 00:00:32.494029", "failed_when_result": true, "item": "vim", "msg": "non-zero return code", "rc": 1, "start": "2025-11-28 00:00:32.481618", "stderr": "", "stderr_lines": [], "stdout": "package vim is not installed", "stdout_lines": ["package vim is not installed"]}
ok: [192.168.219.106] => (item=nano)
ok: [192.168.219.106] => (item=tree)
ok: [192.168.219.106] => (item=jq)

PLAY RECAP **********************************************************************************************************************************************************************************************************************************
192.168.219.106            : ok=7    changed=1    unreachable=0    failed=1    skipped=1    rescued=0    ignored=0
192.168.219.107            : ok=7    changed=1    unreachable=0    failed=1    skipped=1    rescued=0    ignored=0

[root@node1 ansible_lab]# rpm -qa | grep vim
vim-minimal-8.2.2637-22.el9_6.1.x86_64
vim-filesystem-8.2.2637-22.el9_6.1.noarch
vim-common-8.2.2637-22.el9_6.1.x86_64
vim-enhanced-8.2.2637-22.el9_6.1.x86_64
[root@node1 ansible_lab]# vi vars/packages.yml
[root@node1 ansible_lab]# ansible-playbook playbooks/install_packages.yml

PLAY [all] **********************************************************************************************************************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************************************************************************************************
ok: [192.168.219.107]
ok: [192.168.219.106]

TASK [Ensure EPEL repository is enabled] ****************************************************************************************************************************************************************************************************
ok: [192.168.219.107]
ok: [192.168.219.106]

TASK [Refresh DNF/YUM metadata cache] *******************************************************************************************************************************************************************************************************
changed: [192.168.219.106]
changed: [192.168.219.107]

TASK [common_packages : Load package variables] *********************************************************************************************************************************************************************************************
ok: [192.168.219.106]
ok: [192.168.219.107]

TASK [common_packages : Load package variables] *********************************************************************************************************************************************************************************************
skipping: [192.168.219.107]
ok: [192.168.219.106]

TASK [common_packages : Install database server packages] ***********************************************************************************************************************************************************************************
skipping: [192.168.219.106]
ok: [192.168.219.107]

TASK [common_packages : Install base packages on all servers] *******************************************************************************************************************************************************************************
ok: [192.168.219.107]
ok: [192.168.219.106]

TASK [common_packages : include_tasks] ******************************************************************************************************************************************************************************************************
included: /root/ansible_lab/roles/common_packages/tasks/verify.yml for 192.168.219.106, 192.168.219.107

TASK [common_packages : Verify base packages installed] *************************************************************************************************************************************************************************************
ok: [192.168.219.107] => (item=lsof)
ok: [192.168.219.106] => (item=lsof)
ok: [192.168.219.107] => (item=net-tools)
ok: [192.168.219.106] => (item=net-tools)
ok: [192.168.219.107] => (item=sysstat)
ok: [192.168.219.106] => (item=sysstat)
ok: [192.168.219.107] => (item=strace)
ok: [192.168.219.106] => (item=strace)
ok: [192.168.219.107] => (item=htop)
ok: [192.168.219.106] => (item=htop)
ok: [192.168.219.107] => (item=iotop)
ok: [192.168.219.106] => (item=iotop)
ok: [192.168.219.107] => (item=wget)
ok: [192.168.219.107] => (item=curl)
ok: [192.168.219.106] => (item=wget)
ok: [192.168.219.107] => (item=mlocate)
ok: [192.168.219.106] => (item=curl)
ok: [192.168.219.107] => (item=nmap)
ok: [192.168.219.106] => (item=mlocate)
ok: [192.168.219.107] => (item=nmap-ncat)
ok: [192.168.219.106] => (item=nmap)
ok: [192.168.219.107] => (item=tcpdump)
ok: [192.168.219.106] => (item=nmap-ncat)
ok: [192.168.219.107] => (item=bind-utils)
ok: [192.168.219.106] => (item=tcpdump)
ok: [192.168.219.107] => (item=traceroute)
ok: [192.168.219.107] => (item=iperf3)
ok: [192.168.219.106] => (item=bind-utils)
ok: [192.168.219.107] => (item=zip)
ok: [192.168.219.106] => (item=traceroute)
ok: [192.168.219.107] => (item=unzip)
ok: [192.168.219.106] => (item=iperf3)
ok: [192.168.219.107] => (item=tar)
ok: [192.168.219.106] => (item=zip)
ok: [192.168.219.107] => (item=bzip2)
ok: [192.168.219.106] => (item=unzip)
ok: [192.168.219.107] => (item=gzip)
ok: [192.168.219.107] => (item=xz)
ok: [192.168.219.106] => (item=tar)
ok: [192.168.219.107] => (item=p7zip)
ok: [192.168.219.106] => (item=bzip2)
ok: [192.168.219.107] => (item=p7zip-plugins)
ok: [192.168.219.106] => (item=gzip)
ok: [192.168.219.107] => (item=vim-enhanced)
ok: [192.168.219.106] => (item=xz)
ok: [192.168.219.107] => (item=nano)
ok: [192.168.219.106] => (item=p7zip)
ok: [192.168.219.107] => (item=tree)
ok: [192.168.219.107] => (item=jq)
ok: [192.168.219.106] => (item=p7zip-plugins)
ok: [192.168.219.106] => (item=vim-enhanced)
ok: [192.168.219.106] => (item=nano)
ok: [192.168.219.106] => (item=tree)
ok: [192.168.219.106] => (item=jq)

TASK [common_packages : debug] **************************************************************************************************************************************************************************************************************
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'lsof-4.94.0-3.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'lsof'], 'start': '2025-11-28 00:02:45.193244', 'end': '2025-11-28 00:02:45.206841', 'delta': '0:00:00.013597', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q lsof', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['lsof-4.94.0-3.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'lsof', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'lsof' found: lsof-4.94.0-3.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'net-tools-2.0-0.64.20160912git.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'net-tools'], 'start': '2025-11-28 00:02:45.953772', 'end': '2025-11-28 00:02:45.969943', 'delta': '0:00:00.016171', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q net-tools', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['net-tools-2.0-0.64.20160912git.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'net-tools', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'net-tools' found: net-tools-2.0-0.64.20160912git.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'sysstat-12.5.4-9.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'sysstat'], 'start': '2025-11-28 00:02:46.697300', 'end': '2025-11-28 00:02:46.715925', 'delta': '0:00:00.018625', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q sysstat', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['sysstat-12.5.4-9.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'sysstat', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'sysstat' found: sysstat-12.5.4-9.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'strace-6.12-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'strace'], 'start': '2025-11-28 00:02:47.452027', 'end': '2025-11-28 00:02:47.476618', 'delta': '0:00:00.024591', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q strace', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['strace-6.12-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'strace', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'strace' found: strace-6.12-1.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'htop-3.3.0-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'htop'], 'start': '2025-11-28 00:02:48.221407', 'end': '2025-11-28 00:02:48.233301', 'delta': '0:00:00.011894', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q htop', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['htop-3.3.0-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'htop', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'htop' found: htop-3.3.0-1.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'iotop-0.6-30.el9.noarch', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'iotop'], 'start': '2025-11-28 00:02:49.018237', 'end': '2025-11-28 00:02:49.032612', 'delta': '0:00:00.014375', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q iotop', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['iotop-0.6-30.el9.noarch'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'iotop', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'iotop' found: iotop-0.6-30.el9.noarch"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'wget-1.21.1-8.el9_4.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'wget'], 'start': '2025-11-28 00:02:49.784120', 'end': '2025-11-28 00:02:49.798559', 'delta': '0:00:00.014439', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q wget', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['wget-1.21.1-8.el9_4.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'wget', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'wget' found: wget-1.21.1-8.el9_4.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'curl-7.76.1-31.el9_6.1.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'curl'], 'start': '2025-11-28 00:02:50.545201', 'end': '2025-11-28 00:02:50.561807', 'delta': '0:00:00.016606', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q curl', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['curl-7.76.1-31.el9_6.1.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'curl', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'curl' found: curl-7.76.1-31.el9_6.1.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'lsof-4.94.0-3.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'lsof'], 'start': '2025-11-28 00:02:45.129056', 'end': '2025-11-28 00:02:45.148734', 'delta': '0:00:00.019678', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q lsof', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['lsof-4.94.0-3.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'lsof', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'lsof' found: lsof-4.94.0-3.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'net-tools-2.0-0.64.20160912git.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'net-tools'], 'start': '2025-11-28 00:02:45.796429', 'end': '2025-11-28 00:02:45.813199', 'delta': '0:00:00.016770', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q net-tools', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['net-tools-2.0-0.64.20160912git.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'net-tools', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'net-tools' found: net-tools-2.0-0.64.20160912git.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'sysstat-12.5.4-9.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'sysstat'], 'start': '2025-11-28 00:02:46.425821', 'end': '2025-11-28 00:02:46.440749', 'delta': '0:00:00.014928', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q sysstat', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['sysstat-12.5.4-9.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'sysstat', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'sysstat' found: sysstat-12.5.4-9.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'strace-6.12-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'strace'], 'start': '2025-11-28 00:02:47.070767', 'end': '2025-11-28 00:02:47.094826', 'delta': '0:00:00.024059', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q strace', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['strace-6.12-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'strace', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'strace' found: strace-6.12-1.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'htop-3.3.0-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'htop'], 'start': '2025-11-28 00:02:47.714773', 'end': '2025-11-28 00:02:47.734686', 'delta': '0:00:00.019913', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q htop', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['htop-3.3.0-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'htop', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'htop' found: htop-3.3.0-1.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'iotop-0.6-30.el9.noarch', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'iotop'], 'start': '2025-11-28 00:02:48.374783', 'end': '2025-11-28 00:02:48.391389', 'delta': '0:00:00.016606', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q iotop', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['iotop-0.6-30.el9.noarch'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'iotop', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'iotop' found: iotop-0.6-30.el9.noarch"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'wget-1.21.1-8.el9_4.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'wget'], 'start': '2025-11-28 00:02:49.064356', 'end': '2025-11-28 00:02:49.078064', 'delta': '0:00:00.013708', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q wget', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['wget-1.21.1-8.el9_4.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'wget', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'wget' found: wget-1.21.1-8.el9_4.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'mlocate-0.26-30.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'mlocate'], 'start': '2025-11-28 00:02:51.286920', 'end': '2025-11-28 00:02:51.301353', 'delta': '0:00:00.014433', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q mlocate', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['mlocate-0.26-30.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'mlocate', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'mlocate' found: mlocate-0.26-30.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'curl-7.76.1-31.el9_6.1.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'curl'], 'start': '2025-11-28 00:02:49.688103', 'end': '2025-11-28 00:02:49.701847', 'delta': '0:00:00.013744', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q curl', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['curl-7.76.1-31.el9_6.1.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'curl', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'curl' found: curl-7.76.1-31.el9_6.1.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'mlocate-0.26-30.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'mlocate'], 'start': '2025-11-28 00:02:50.351226', 'end': '2025-11-28 00:02:50.365306', 'delta': '0:00:00.014080', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q mlocate', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['mlocate-0.26-30.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'mlocate', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'mlocate' found: mlocate-0.26-30.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'nmap-7.92-3.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'nmap'], 'start': '2025-11-28 00:02:51.996088', 'end': '2025-11-28 00:02:52.017535', 'delta': '0:00:00.021447', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q nmap', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['nmap-7.92-3.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'nmap', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'nmap' found: nmap-7.92-3.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'nmap-7.92-3.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'nmap'], 'start': '2025-11-28 00:02:50.993257', 'end': '2025-11-28 00:02:51.010098', 'delta': '0:00:00.016841', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q nmap', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['nmap-7.92-3.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'nmap', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'nmap' found: nmap-7.92-3.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'nmap-ncat-7.92-3.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'nmap-ncat'], 'start': '2025-11-28 00:02:52.757791', 'end': '2025-11-28 00:02:52.776245', 'delta': '0:00:00.018454', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q nmap-ncat', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['nmap-ncat-7.92-3.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'nmap-ncat', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'nmap-ncat' found: nmap-ncat-7.92-3.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'nmap-ncat-7.92-3.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'nmap-ncat'], 'start': '2025-11-28 00:02:51.623194', 'end': '2025-11-28 00:02:51.639063', 'delta': '0:00:00.015869', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q nmap-ncat', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['nmap-ncat-7.92-3.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'nmap-ncat', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'nmap-ncat' found: nmap-ncat-7.92-3.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'tcpdump-4.99.0-9.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tcpdump'], 'start': '2025-11-28 00:02:52.252239', 'end': '2025-11-28 00:02:52.270316', 'delta': '0:00:00.018077', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tcpdump', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tcpdump-4.99.0-9.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tcpdump', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'tcpdump' found: tcpdump-4.99.0-9.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'tcpdump-4.99.0-9.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tcpdump'], 'start': '2025-11-28 00:02:53.533567', 'end': '2025-11-28 00:02:53.552563', 'delta': '0:00:00.018996', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tcpdump', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tcpdump-4.99.0-9.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tcpdump', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'tcpdump' found: tcpdump-4.99.0-9.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'bind-utils-9.16.23-31.el9_6.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'bind-utils'], 'start': '2025-11-28 00:02:52.900234', 'end': '2025-11-28 00:02:52.916050', 'delta': '0:00:00.015816', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q bind-utils', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['bind-utils-9.16.23-31.el9_6.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'bind-utils', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'bind-utils' found: bind-utils-9.16.23-31.el9_6.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'traceroute-2.1.1-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'traceroute'], 'start': '2025-11-28 00:02:53.593192', 'end': '2025-11-28 00:02:53.607677', 'delta': '0:00:00.014485', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q traceroute', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['traceroute-2.1.1-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'traceroute', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'traceroute' found: traceroute-2.1.1-1.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'bind-utils-9.16.23-31.el9_6.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'bind-utils'], 'start': '2025-11-28 00:02:54.318442', 'end': '2025-11-28 00:02:54.332445', 'delta': '0:00:00.014003', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q bind-utils', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['bind-utils-9.16.23-31.el9_6.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'bind-utils', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'bind-utils' found: bind-utils-9.16.23-31.el9_6.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'iperf3-3.9-14.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'iperf3'], 'start': '2025-11-28 00:02:54.279768', 'end': '2025-11-28 00:02:54.295810', 'delta': '0:00:00.016042', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q iperf3', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['iperf3-3.9-14.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'iperf3', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'iperf3' found: iperf3-3.9-14.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'traceroute-2.1.1-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'traceroute'], 'start': '2025-11-28 00:02:55.103784', 'end': '2025-11-28 00:02:55.121051', 'delta': '0:00:00.017267', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q traceroute', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['traceroute-2.1.1-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'traceroute', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'traceroute' found: traceroute-2.1.1-1.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'zip-3.0-35.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'zip'], 'start': '2025-11-28 00:02:54.924000', 'end': '2025-11-28 00:02:54.940360', 'delta': '0:00:00.016360', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q zip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['zip-3.0-35.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'zip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'zip' found: zip-3.0-35.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'unzip-6.0-58.el9_5.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'unzip'], 'start': '2025-11-28 00:02:55.572772', 'end': '2025-11-28 00:02:55.586653', 'delta': '0:00:00.013881', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q unzip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['unzip-6.0-58.el9_5.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'unzip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'unzip' found: unzip-6.0-58.el9_5.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'iperf3-3.9-14.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'iperf3'], 'start': '2025-11-28 00:02:55.863513', 'end': '2025-11-28 00:02:55.877164', 'delta': '0:00:00.013651', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q iperf3', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['iperf3-3.9-14.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'iperf3', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'iperf3' found: iperf3-3.9-14.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'tar-1.34-7.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tar'], 'start': '2025-11-28 00:02:56.200224', 'end': '2025-11-28 00:02:56.216373', 'delta': '0:00:00.016149', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tar', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tar-1.34-7.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tar', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'tar' found: tar-1.34-7.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'bzip2-1.0.8-10.el9_5.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'bzip2'], 'start': '2025-11-28 00:02:56.822025', 'end': '2025-11-28 00:02:56.835699', 'delta': '0:00:00.013674', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q bzip2', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['bzip2-1.0.8-10.el9_5.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'bzip2', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'bzip2' found: bzip2-1.0.8-10.el9_5.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'zip-3.0-35.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'zip'], 'start': '2025-11-28 00:02:56.597728', 'end': '2025-11-28 00:02:56.610392', 'delta': '0:00:00.012664', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q zip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['zip-3.0-35.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'zip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'zip' found: zip-3.0-35.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'gzip-1.12-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'gzip'], 'start': '2025-11-28 00:02:57.437730', 'end': '2025-11-28 00:02:57.457323', 'delta': '0:00:00.019593', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q gzip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['gzip-1.12-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'gzip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'gzip' found: gzip-1.12-1.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'xz-5.2.5-8.el9_0.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'xz'], 'start': '2025-11-28 00:02:58.075080', 'end': '2025-11-28 00:02:58.089903', 'delta': '0:00:00.014823', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q xz', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['xz-5.2.5-8.el9_0.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'xz', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'xz' found: xz-5.2.5-8.el9_0.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'unzip-6.0-58.el9_5.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'unzip'], 'start': '2025-11-28 00:02:57.334831', 'end': '2025-11-28 00:02:57.351007', 'delta': '0:00:00.016176', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q unzip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['unzip-6.0-58.el9_5.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'unzip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'unzip' found: unzip-6.0-58.el9_5.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'p7zip-16.02-31.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'p7zip'], 'start': '2025-11-28 00:02:58.694885', 'end': '2025-11-28 00:02:58.709883', 'delta': '0:00:00.014998', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q p7zip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['p7zip-16.02-31.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'p7zip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'p7zip' found: p7zip-16.02-31.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'p7zip-plugins-16.02-31.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'p7zip-plugins'], 'start': '2025-11-28 00:02:59.315993', 'end': '2025-11-28 00:02:59.332627', 'delta': '0:00:00.016634', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q p7zip-plugins', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['p7zip-plugins-16.02-31.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'p7zip-plugins', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'p7zip-plugins' found: p7zip-plugins-16.02-31.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'vim-enhanced-8.2.2637-22.el9_6.1.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'vim-enhanced'], 'start': '2025-11-28 00:02:59.971916', 'end': '2025-11-28 00:02:59.984711', 'delta': '0:00:00.012795', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q vim-enhanced', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['vim-enhanced-8.2.2637-22.el9_6.1.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'vim-enhanced', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'vim-enhanced' found: vim-enhanced-8.2.2637-22.el9_6.1.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'nano-5.6.1-7.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'nano'], 'start': '2025-11-28 00:03:00.599621', 'end': '2025-11-28 00:03:00.620162', 'delta': '0:00:00.020541', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q nano', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['nano-5.6.1-7.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'nano', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'nano' found: nano-5.6.1-7.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'tree-1.8.0-10.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tree'], 'start': '2025-11-28 00:03:01.209789', 'end': '2025-11-28 00:03:01.226342', 'delta': '0:00:00.016553', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tree', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tree-1.8.0-10.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tree', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'tree' found: tree-1.8.0-10.el9.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'jq-1.6-17.el9_6.2.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'jq'], 'start': '2025-11-28 00:03:01.851521', 'end': '2025-11-28 00:03:01.865962', 'delta': '0:00:00.014441', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q jq', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['jq-1.6-17.el9_6.2.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'jq', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'jq' found: jq-1.6-17.el9_6.2.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'tar-1.34-7.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tar'], 'start': '2025-11-28 00:02:58.114877', 'end': '2025-11-28 00:02:58.129601', 'delta': '0:00:00.014724', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tar', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tar-1.34-7.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tar', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'tar' found: tar-1.34-7.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'bzip2-1.0.8-10.el9_5.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'bzip2'], 'start': '2025-11-28 00:02:58.854894', 'end': '2025-11-28 00:02:58.867138', 'delta': '0:00:00.012244', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q bzip2', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['bzip2-1.0.8-10.el9_5.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'bzip2', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'bzip2' found: bzip2-1.0.8-10.el9_5.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'gzip-1.12-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'gzip'], 'start': '2025-11-28 00:02:59.677587', 'end': '2025-11-28 00:02:59.695959', 'delta': '0:00:00.018372', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q gzip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['gzip-1.12-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'gzip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'gzip' found: gzip-1.12-1.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'xz-5.2.5-8.el9_0.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'xz'], 'start': '2025-11-28 00:03:00.426897', 'end': '2025-11-28 00:03:00.439522', 'delta': '0:00:00.012625', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q xz', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['xz-5.2.5-8.el9_0.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'xz', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'xz' found: xz-5.2.5-8.el9_0.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'p7zip-16.02-31.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'p7zip'], 'start': '2025-11-28 00:03:01.160081', 'end': '2025-11-28 00:03:01.173838', 'delta': '0:00:00.013757', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q p7zip', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['p7zip-16.02-31.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'p7zip', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'p7zip' found: p7zip-16.02-31.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'p7zip-plugins-16.02-31.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'p7zip-plugins'], 'start': '2025-11-28 00:03:01.895083', 'end': '2025-11-28 00:03:01.908572', 'delta': '0:00:00.013489', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q p7zip-plugins', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['p7zip-plugins-16.02-31.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'p7zip-plugins', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'p7zip-plugins' found: p7zip-plugins-16.02-31.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'vim-enhanced-8.2.2637-22.el9_6.1.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'vim-enhanced'], 'start': '2025-11-28 00:03:02.595957', 'end': '2025-11-28 00:03:02.608962', 'delta': '0:00:00.013005', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q vim-enhanced', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['vim-enhanced-8.2.2637-22.el9_6.1.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'vim-enhanced', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'vim-enhanced' found: vim-enhanced-8.2.2637-22.el9_6.1.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'nano-5.6.1-7.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'nano'], 'start': '2025-11-28 00:03:03.402912', 'end': '2025-11-28 00:03:03.415573', 'delta': '0:00:00.012661', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q nano', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['nano-5.6.1-7.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'nano', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'nano' found: nano-5.6.1-7.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'tree-1.8.0-10.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tree'], 'start': '2025-11-28 00:03:04.110348', 'end': '2025-11-28 00:03:04.123019', 'delta': '0:00:00.012671', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tree', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tree-1.8.0-10.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tree', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'tree' found: tree-1.8.0-10.el9.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'jq-1.6-17.el9_6.2.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'jq'], 'start': '2025-11-28 00:03:04.852446', 'end': '2025-11-28 00:03:04.864862', 'delta': '0:00:00.012416', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q jq', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['jq-1.6-17.el9_6.2.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'jq', 'ansible_loop_var': 'item'}) => {
    "msg": "Base package 'jq' found: jq-1.6-17.el9_6.2.x86_64"
}

TASK [common_packages : Verify web packages installed] **************************************************************************************************************************************************************************************
skipping: [192.168.219.107] => (item=httpd)
skipping: [192.168.219.107] => (item=httpd-tools)
skipping: [192.168.219.107] => (item=mod_ssl)
skipping: [192.168.219.107] => (item=java-17-openjdk)
skipping: [192.168.219.107] => (item=java-17-openjdk-devel)
skipping: [192.168.219.107] => (item=tomcat)
skipping: [192.168.219.107] => (item=tomcat-admin-webapps)
skipping: [192.168.219.107] => (item=tomcat-webapps)
skipping: [192.168.219.107]
ok: [192.168.219.106] => (item=httpd)
ok: [192.168.219.106] => (item=httpd-tools)
ok: [192.168.219.106] => (item=mod_ssl)
ok: [192.168.219.106] => (item=java-17-openjdk)
ok: [192.168.219.106] => (item=java-17-openjdk-devel)
ok: [192.168.219.106] => (item=tomcat)
ok: [192.168.219.106] => (item=tomcat-admin-webapps)
ok: [192.168.219.106] => (item=tomcat-webapps)

TASK [common_packages : debug] **************************************************************************************************************************************************************************************************************
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'httpd', 'ansible_loop_var': 'item'})
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'httpd-2.4.62-4.el9_6.4.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'httpd'], 'start': '2025-11-28 00:03:05.925802', 'end': '2025-11-28 00:03:05.937990', 'delta': '0:00:00.012188', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q httpd', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['httpd-2.4.62-4.el9_6.4.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'httpd', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'httpd' found: httpd-2.4.62-4.el9_6.4.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'httpd-tools-2.4.62-4.el9_6.4.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'httpd-tools'], 'start': '2025-11-28 00:03:06.639263', 'end': '2025-11-28 00:03:06.652601', 'delta': '0:00:00.013338', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q httpd-tools', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['httpd-tools-2.4.62-4.el9_6.4.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'httpd-tools', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'httpd-tools' found: httpd-tools-2.4.62-4.el9_6.4.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'mod_ssl-2.4.62-4.el9_6.4.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'mod_ssl'], 'start': '2025-11-28 00:03:07.358645', 'end': '2025-11-28 00:03:07.372960', 'delta': '0:00:00.014315', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q mod_ssl', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['mod_ssl-2.4.62-4.el9_6.4.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'mod_ssl', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'mod_ssl' found: mod_ssl-2.4.62-4.el9_6.4.x86_64"
}
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'java-17-openjdk-17.0.17.0.10-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'java-17-openjdk'], 'start': '2025-11-28 00:03:08.178886', 'end': '2025-11-28 00:03:08.193405', 'delta': '0:00:00.014519', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q java-17-openjdk', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['java-17-openjdk-17.0.17.0.10-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'java-17-openjdk', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'java-17-openjdk' found: java-17-openjdk-17.0.17.0.10-1.el9.x86_64"
}
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'httpd-tools', 'ansible_loop_var': 'item'})
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'java-17-openjdk-devel-17.0.17.0.10-1.el9.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'java-17-openjdk-devel'], 'start': '2025-11-28 00:03:08.898483', 'end': '2025-11-28 00:03:08.911035', 'delta': '0:00:00.012552', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q java-17-openjdk-devel', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['java-17-openjdk-devel-17.0.17.0.10-1.el9.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'java-17-openjdk-devel', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'java-17-openjdk-devel' found: java-17-openjdk-devel-17.0.17.0.10-1.el9.x86_64"
}
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'mod_ssl', 'ansible_loop_var': 'item'})
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'java-17-openjdk', 'ansible_loop_var': 'item'})
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'tomcat-9.0.87-3.el9_6.3.noarch', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tomcat'], 'start': '2025-11-28 00:03:09.638812', 'end': '2025-11-28 00:03:09.653927', 'delta': '0:00:00.015115', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tomcat', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tomcat-9.0.87-3.el9_6.3.noarch'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tomcat', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'tomcat' found: tomcat-9.0.87-3.el9_6.3.noarch"
}
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'java-17-openjdk-devel', 'ansible_loop_var': 'item'})
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'tomcat', 'ansible_loop_var': 'item'})
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'tomcat-admin-webapps', 'ansible_loop_var': 'item'})
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'tomcat-admin-webapps-9.0.87-3.el9_6.3.noarch', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tomcat-admin-webapps'], 'start': '2025-11-28 00:03:10.377915', 'end': '2025-11-28 00:03:10.393062', 'delta': '0:00:00.015147', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tomcat-admin-webapps', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tomcat-admin-webapps-9.0.87-3.el9_6.3.noarch'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tomcat-admin-webapps', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'tomcat-admin-webapps' found: tomcat-admin-webapps-9.0.87-3.el9_6.3.noarch"
}
skipping: [192.168.219.107] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'tomcat-webapps', 'ansible_loop_var': 'item'})
ok: [192.168.219.106] => (item={'changed': False, 'stdout': 'tomcat-webapps-9.0.87-3.el9_6.3.noarch', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'tomcat-webapps'], 'start': '2025-11-28 00:03:11.126820', 'end': '2025-11-28 00:03:11.138855', 'delta': '0:00:00.012035', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q tomcat-webapps', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['tomcat-webapps-9.0.87-3.el9_6.3.noarch'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'tomcat-webapps', 'ansible_loop_var': 'item'}) => {
    "msg": "Web package 'tomcat-webapps' found: tomcat-webapps-9.0.87-3.el9_6.3.noarch"
}
skipping: [192.168.219.107]

TASK [common_packages : Verify db packages installed] ***************************************************************************************************************************************************************************************
skipping: [192.168.219.106] => (item=mariadb)
skipping: [192.168.219.106] => (item=mariadb-server)
skipping: [192.168.219.106] => (item=mariadb-backup)
skipping: [192.168.219.106]
ok: [192.168.219.107] => (item=mariadb)
ok: [192.168.219.107] => (item=mariadb-server)
ok: [192.168.219.107] => (item=mariadb-backup)

TASK [common_packages : debug] **************************************************************************************************************************************************************************************************************
skipping: [192.168.219.106] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'mariadb', 'ansible_loop_var': 'item'})
skipping: [192.168.219.106] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'mariadb-server', 'ansible_loop_var': 'item'})
skipping: [192.168.219.106] => (item={'changed': False, 'skipped': True, 'skip_reason': 'Conditional result was False', 'item': 'mariadb-backup', 'ansible_loop_var': 'item'})
skipping: [192.168.219.106]
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'mariadb-10.5.29-2.el9_6.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'mariadb'], 'start': '2025-11-28 00:03:11.859695', 'end': '2025-11-28 00:03:11.871842', 'delta': '0:00:00.012147', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q mariadb', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['mariadb-10.5.29-2.el9_6.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'mariadb', 'ansible_loop_var': 'item'}) => {
    "msg": "DB package 'mariadb' found: mariadb-10.5.29-2.el9_6.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'mariadb-server-10.5.29-2.el9_6.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'mariadb-server'], 'start': '2025-11-28 00:03:12.467800', 'end': '2025-11-28 00:03:12.487897', 'delta': '0:00:00.020097', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q mariadb-server', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['mariadb-server-10.5.29-2.el9_6.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'mariadb-server', 'ansible_loop_var': 'item'}) => {
    "msg": "DB package 'mariadb-server' found: mariadb-server-10.5.29-2.el9_6.x86_64"
}
ok: [192.168.219.107] => (item={'changed': False, 'stdout': 'mariadb-backup-10.5.29-2.el9_6.x86_64', 'stderr': '', 'rc': 0, 'cmd': ['rpm', '-q', 'mariadb-backup'], 'start': '2025-11-28 00:03:13.093823', 'end': '2025-11-28 00:03:13.105176', 'delta': '0:00:00.011353', 'msg': '', 'invocation': {'module_args': {'_raw_params': 'rpm -q mariadb-backup', '_uses_shell': False, 'stdin_add_newline': True, 'strip_empty_ends': True, 'argv': None, 'chdir': None, 'executable': None, 'creates': None, 'removes': None, 'stdin': None}}, 'stdout_lines': ['mariadb-backup-10.5.29-2.el9_6.x86_64'], 'stderr_lines': [], 'failed': False, 'failed_when_result': False, 'item': 'mariadb-backup', 'ansible_loop_var': 'item'}) => {
    "msg": "DB package 'mariadb-backup' found: mariadb-backup-10.5.29-2.el9_6.x86_64"
}

PLAY RECAP **********************************************************************************************************************************************************************************************************************************
192.168.219.106            : ok=11   changed=1    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
192.168.219.107            : ok=11   changed=1    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0

```
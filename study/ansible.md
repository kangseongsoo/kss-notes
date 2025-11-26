# Ansible 완전 정리 가이드

## 1. Ansible이란?

### 1.1 정의
Ansible은 **인프라 자동화 및 구성 관리 도구**입니다. SSH를 통해 원격 서버에 명령을 실행하고, 서버 설정을 자동화할 수 있습니다.

### 1.2 주요 특징
- **Agentless**: 대상 서버에 별도 에이전트 설치 불필요 (SSH만 있으면 됨)
- **선언적(Declarative)**: 원하는 상태를 선언하면 Ansible이 그 상태로 만듦
- **Idempotent**: 여러 번 실행해도 결과가 동일 (멱등성 보장)
- **YAML 기반**: 읽기 쉽고 작성하기 쉬운 YAML 문법 사용
- **Python 기반**: Python으로 작성되어 확장성 좋음

### 1.3 동작 원리
```
Control Node (Ansible 설치된 서버)
    ↓ SSH 연결
Target Nodes (관리 대상 서버들)
```

1. Control Node에서 Playbook 실행
2. SSH로 Target Node에 연결
3. Python 모듈을 임시로 전송하여 실행
4. 결과를 수집하여 Control Node로 반환

---

## 2. 설치 및 기본 설정

### 2.1 설치 방법

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ansible -y
```

#### CentOS/RHEL
```bash
sudo yum install epel-release -y
sudo yum install ansible -y
```

#### Python pip로 설치
```bash
pip install ansible
```

### 2.2 버전 확인
```bash
ansible --version
```

### 2.3 기본 디렉토리 구조
```
ansible-project/
├── inventory/          # 서버 목록
│   └── hosts.yml
├── playbooks/          # Playbook 파일들
│   └── site.yml
├── roles/              # 재사용 가능한 역할들
│   └── common/
├── group_vars/         # 그룹별 변수
│   └── all.yml
├── host_vars/          # 호스트별 변수
│   └── server1.yml
└── ansible.cfg         # Ansible 설정 파일
```

---

## 3. 핵심 개념

### 3.1 Inventory (인벤토리)
관리할 서버들의 목록을 정의하는 파일입니다.

**기본 형식 (INI 스타일)**
```ini
[webservers]
web1.example.com
web2.example.com ansible_host=192.168.1.10

[dbservers]
db1.example.com
db2.example.com

[webservers:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_rsa
```

**YAML 형식 (권장)**
```yaml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 192.168.1.10
          ansible_user: ubuntu
        web2:
          ansible_host: 192.168.1.11
          ansible_user: ubuntu
    dbservers:
      hosts:
        db1:
          ansible_host: 192.168.1.20
          ansible_user: root
      vars:
        db_port: 3306
```

### 3.2 Playbook
작업을 정의하는 YAML 파일입니다. 하나 이상의 Play로 구성됩니다.

**기본 구조**
```yaml
---
- name: Play 이름
  hosts: webservers
  become: yes
  tasks:
    - name: 작업 설명
      module_name:
        parameter: value
```

### 3.3 Module (모듈)
Ansible이 실행하는 작업 단위입니다. 각 모듈은 특정 작업을 수행합니다.

**주요 모듈**
- `apt`, `yum`: 패키지 관리
- `copy`, `template`: 파일 복사/템플릿
- `service`, `systemd`: 서비스 관리
- `user`, `group`: 사용자/그룹 관리
- `file`: 파일/디렉토리 관리
- `command`, `shell`: 명령 실행
- `git`: Git 저장소 클론
- `docker_container`: Docker 컨테이너 관리

### 3.4 Task
하나의 작업 단위입니다. 모듈을 사용하여 정의합니다.

### 3.5 Role
재사용 가능한 작업 묶음입니다. 관련된 Task, Handler, 변수, 파일을 구조화하여 관리합니다.

**Role 구조**
```
roles/
└── nginx/
    ├── tasks/
    │   └── main.yml
    ├── handlers/
    │   └── main.yml
    ├── templates/
    │   └── nginx.conf.j2
    ├── files/
    ├── vars/
    │   └── main.yml
    ├── defaults/
    │   └── main.yml
    └── meta/
        └── main.yml
```

### 3.6 Handler
특정 조건에서만 실행되는 작업입니다. 보통 서비스 재시작 등에 사용됩니다.

---

## 4. 문법 상세

### 4.1 Playbook 기본 문법

```yaml
---
- name: 웹서버 설정
  hosts: webservers
  become: yes                    # sudo 권한 사용
  gather_facts: yes              # 시스템 정보 수집 (기본값: yes)
  vars:                          # 변수 정의
    http_port: 80
    max_clients: 200
  
  tasks:
    - name: Nginx 설치
      apt:
        name: nginx
        state: present
        update_cache: yes
    
    - name: Nginx 설정 파일 복사
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: restart nginx      # Handler 트리거
    
    - name: Nginx 서비스 시작
      systemd:
        name: nginx
        state: started
        enabled: yes
  
  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted
```

### 4.2 변수 (Variables)

#### 변수 정의 방법

**1. Playbook 내부에서 정의**
```yaml
vars:
  package_name: nginx
  config_file: /etc/nginx/nginx.conf
```

**2. Inventory에서 정의**
```yaml
all:
  vars:
    ansible_user: ubuntu
  hosts:
    web1:
      vars:
        server_name: example.com
```

**3. group_vars/host_vars 파일**
```yaml
# group_vars/webservers.yml
nginx_version: 1.20.1
max_workers: 4

# host_vars/web1.yml
server_name: web1.example.com
```

**4. 명령줄에서 전달**
```bash
ansible-playbook playbook.yml -e "package_name=apache2"
```

**5. 변수 파일 사용**
```yaml
vars_files:
  - vars/main.yml
```

#### 변수 사용
```yaml
tasks:
  - name: 패키지 설치
    apt:
      name: "{{ package_name }}"
      state: present
  
  - name: 변수 출력
    debug:
      msg: "서버 이름은 {{ server_name }}입니다"
```

#### 특수 변수
- `ansible_hostname`: 호스트명
- `ansible_os_family`: OS 계열 (RedHat, Debian 등)
- `ansible_distribution`: 배포판 이름 (Ubuntu, CentOS 등)
- `ansible_default_ipv4.address`: 기본 IP 주소
- `inventory_hostname`: Inventory에 정의된 호스트명

### 4.3 조건문 (Conditionals)

#### when 사용
```yaml
tasks:
  - name: Debian 계열에서만 실행
    apt:
      name: nginx
      state: present
    when: ansible_os_family == "Debian"
  
  - name: RedHat 계열에서만 실행
    yum:
      name: nginx
      state: present
    when: ansible_os_family == "RedHat"
  
  - name: 파일이 존재할 때만 실행
    copy:
      src: config.conf
      dest: /etc/config.conf
    when: ansible_distribution == "Ubuntu"
  
  - name: 여러 조건
    command: /usr/bin/something
    when:
      - ansible_os_family == "Debian"
      - ansible_distribution_version == "20.04"
```

#### 조건 연산자
```yaml
when:
  - condition1
  - condition2          # AND (모두 참)
  
when: condition1 or condition2    # OR
when: not condition1              # NOT
when: value is defined            # 변수 정의 여부
when: value is not defined
when: value | length > 0          # 리스트/문자열 길이
```

### 4.4 반복문 (Loops)

#### loop 사용
```yaml
tasks:
  - name: 여러 패키지 설치
    apt:
      name: "{{ item }}"
      state: present
    loop:
      - nginx
      - mysql-server
      - php-fpm
  
  - name: 사용자 생성
    user:
      name: "{{ item.name }}"
      uid: "{{ item.uid }}"
      groups: "{{ item.groups }}"
    loop:
      - name: user1
        uid: 1001
        groups: sudo
      - name: user2
        uid: 1002
        groups: docker
  
  - name: 파일 복사
    copy:
      src: "{{ item.src }}"
      dest: "{{ item.dest }}"
      mode: "{{ item.mode }}"
    loop:
      - { src: file1.conf, dest: /etc/file1.conf, mode: '0644' }
      - { src: file2.conf, dest: /etc/file2.conf, mode: '0755' }
```

#### with_items (구버전, 여전히 사용 가능)
```yaml
tasks:
  - name: 패키지 설치
    apt:
      name: "{{ item }}"
      state: present
    with_items:
      - nginx
      - mysql-server
```

#### 딕셔너리 반복
```yaml
tasks:
  - name: 디렉토리 생성
    file:
      path: "{{ item.key }}"
      state: directory
      mode: "{{ item.value }}"
    loop: "{{ dirs | dict2items }}"
  vars:
    dirs:
      /var/www: '0755'
      /var/log: '0750'
```

### 4.5 템플릿 (Jinja2)

#### 템플릿 파일 생성
```jinja2
# templates/nginx.conf.j2
server {
    listen {{ http_port }};
    server_name {{ server_name }};
    
    {% if ssl_enabled %}
    listen 443 ssl;
    ssl_certificate {{ ssl_cert_path }};
    ssl_certificate_key {{ ssl_key_path }};
    {% endif %}
    
    location / {
        proxy_pass http://{{ backend_host }}:{{ backend_port }};
    }
    
    access_log /var/log/nginx/{{ server_name }}.access.log;
    error_log /var/log/nginx/{{ server_name }}.error.log;
}
```

#### 템플릿 사용
```yaml
tasks:
  - name: Nginx 설정 파일 생성
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/sites-available/{{ server_name }}
      mode: '0644'
    notify: restart nginx
```

#### Jinja2 필터
```yaml
tasks:
  - name: 필터 사용 예제
    debug:
      msg: |
        대문자: {{ server_name | upper }}
        소문자: {{ server_name | lower }}
        기본값: {{ undefined_var | default('기본값') }}
        리스트 조인: {{ list_var | join(',') }}
        파일명: {{ path | basename }}
        디렉토리: {{ path | dirname }}
```

### 4.6 에러 처리

#### ignore_errors
```yaml
tasks:
  - name: 실패해도 계속 진행
    command: /usr/bin/maybe-fails
    ignore_errors: yes
```

#### failed_when / changed_when
```yaml
tasks:
  - name: 커스텀 실패 조건
    command: /usr/bin/check-status
    register: result
    failed_when: "'ERROR' in result.stdout"
    changed_when: false
  
  - name: 커스텀 변경 조건
    command: /usr/bin/update
    register: result
    changed_when: "'Updated' in result.stdout"
```

#### 블록과 에러 처리
```yaml
tasks:
  - name: 블록 시작
    block:
      - name: 작업 1
        command: /usr/bin/task1
      
      - name: 작업 2
        command: /usr/bin/task2
    
    rescue:
      - name: 에러 발생 시 실행
        debug:
          msg: "에러가 발생했습니다"
    
    always:
      - name: 항상 실행
        debug:
          msg: "블록 완료"
```

### 4.7 태그 (Tags)

```yaml
tasks:
  - name: 패키지 설치
    apt:
      name: nginx
      state: present
    tags:
      - packages
      - nginx
  
  - name: 설정 파일 복사
    copy:
      src: config.conf
      dest: /etc/config.conf
    tags:
      - config
  
  - name: 서비스 시작
    systemd:
      name: nginx
      state: started
    tags:
      - service
```

**태그로 실행**
```bash
# 특정 태그만 실행
ansible-playbook playbook.yml --tags "packages,config"

# 특정 태그 제외
ansible-playbook playbook.yml --skip-tags "service"
```

---

## 5. 주요 모듈 상세

### 5.1 패키지 관리

#### apt (Debian/Ubuntu)
```yaml
tasks:
  - name: 패키지 설치
    apt:
      name: nginx
      state: present
  
  - name: 여러 패키지 설치
    apt:
      name:
        - nginx
        - mysql-server
      state: present
      update_cache: yes
  
  - name: 패키지 제거
    apt:
      name: apache2
      state: absent
  
  - name: 최신 버전으로 업그레이드
    apt:
      name: nginx
      state: latest
  
  - name: 전체 시스템 업그레이드
    apt:
      upgrade: dist
      update_cache: yes
```

#### yum (RedHat/CentOS)
```yaml
tasks:
  - name: 패키지 설치
    yum:
      name: nginx
      state: present
  
  - name: 최신 버전으로 업그레이드
    yum:
      name: nginx
      state: latest
```

### 5.2 파일 관리

#### copy
```yaml
tasks:
  - name: 파일 복사
    copy:
      src: files/config.conf
      dest: /etc/config.conf
      mode: '0644'
      owner: root
      group: root
      backup: yes  # 기존 파일 백업
```

#### template
```yaml
tasks:
  - name: 템플릿 파일 생성
    template:
      src: templates/nginx.conf.j2
      dest: /etc/nginx/nginx.conf
      mode: '0644'
      owner: root
      group: root
```

#### file
```yaml
tasks:
  - name: 디렉토리 생성
    file:
      path: /var/www/html
      state: directory
      mode: '0755'
      owner: www-data
      group: www-data
  
  - name: 심볼릭 링크 생성
    file:
      src: /etc/nginx/sites-available/example
      dest: /etc/nginx/sites-enabled/example
      state: link
  
  - name: 파일 삭제
    file:
      path: /tmp/oldfile.txt
      state: absent
```

### 5.3 서비스 관리

#### systemd
```yaml
tasks:
  - name: 서비스 시작
    systemd:
      name: nginx
      state: started
      enabled: yes  # 부팅 시 자동 시작
  
  - name: 서비스 중지
    systemd:
      name: nginx
      state: stopped
  
  - name: 서비스 재시작
    systemd:
      name: nginx
      state: restarted
  
  - name: 서비스 리로드
    systemd:
      name: nginx
      state: reloaded
```

### 5.4 사용자/그룹 관리

#### user
```yaml
tasks:
  - name: 사용자 생성
    user:
      name: deploy
      uid: 1001
      group: developers
      groups: sudo,docker
      shell: /bin/bash
      home: /home/deploy
      create_home: yes
      generate_ssh_key: yes
      ssh_key_type: rsa
      ssh_key_bits: 2048
  
  - name: 사용자 삭제
    user:
      name: olduser
      state: absent
      remove: yes  # 홈 디렉토리도 삭제
```

#### group
```yaml
tasks:
  - name: 그룹 생성
    group:
      name: developers
      state: present
      gid: 2001
```

### 5.5 명령 실행

#### command
```yaml
tasks:
  - name: 명령 실행 (셸 기능 사용 안 함)
    command: /usr/bin/script.sh arg1 arg2
    args:
      chdir: /tmp
      creates: /tmp/result.txt  # 파일이 있으면 실행 안 함
```

#### shell
```yaml
tasks:
  - name: 셸 명령 실행
    shell: |
      cd /var/www
      tar -xzf archive.tar.gz
      chmod +x script.sh
    args:
      executable: /bin/bash
```

#### raw
```yaml
tasks:
  - name: Python이 없는 서버에서 실행
    raw: yum install -y python3
```

### 5.6 Git 관리

#### git
```yaml
tasks:
  - name: Git 저장소 클론
    git:
      repo: https://github.com/user/repo.git
      dest: /var/www/app
      version: main
      update: yes
  
  - name: 특정 브랜치 클론
    git:
      repo: https://github.com/user/repo.git
      dest: /var/www/app
      version: develop
      force: yes
```

---

## 6. 실무 예제

### 6.1 기본 웹서버 설정

```yaml
---
- name: Nginx 웹서버 설정
  hosts: webservers
  become: yes
  vars:
    nginx_user: www-data
    document_root: /var/www/html
  
  tasks:
    - name: Nginx 설치
      apt:
        name: nginx
        state: present
        update_cache: yes
    
    - name: 기본 설정 파일 백업
      copy:
        src: /etc/nginx/sites-available/default
        dest: /etc/nginx/sites-available/default.backup
        remote_src: yes
      when: ansible_os_family == "Debian"
    
    - name: 웹 루트 디렉토리 생성
      file:
        path: "{{ document_root }}"
        state: directory
        owner: "{{ nginx_user }}"
        group: "{{ nginx_user }}"
        mode: '0755'
    
    - name: 기본 index.html 생성
      copy:
        content: |
          <!DOCTYPE html>
          <html>
          <head>
              <title>Welcome to {{ inventory_hostname }}</title>
          </head>
          <body>
              <h1>Hello from Ansible!</h1>
          </body>
          </html>
        dest: "{{ document_root }}/index.html"
        owner: "{{ nginx_user }}"
        group: "{{ nginx_user }}"
        mode: '0644'
    
    - name: Nginx 서비스 시작 및 활성화
      systemd:
        name: nginx
        state: started
        enabled: yes
    
    - name: 방화벽 포트 열기
      ufw:
        rule: allow
        port: '80'
        proto: tcp
      when: ansible_os_family == "Debian"
```

### 6.2 데이터베이스 서버 설정

```yaml
---
- name: MySQL 서버 설정
  hosts: dbservers
  become: yes
  vars:
    mysql_root_password: "{{ vault_mysql_root_password }}"
    mysql_db: myapp
    mysql_user: appuser
    mysql_password: "{{ vault_mysql_password }}"
  
  tasks:
    - name: MySQL 서버 설치
      apt:
        name: mysql-server
        state: present
        update_cache: yes
    
    - name: MySQL 보안 설정
      mysql_user:
        name: root
        password: "{{ mysql_root_password }}"
        host: localhost
        login_user: root
        login_password: ""
        check_implicit_admin: yes
    
    - name: 데이터베이스 생성
      mysql_db:
        name: "{{ mysql_db }}"
        state: present
        login_user: root
        login_password: "{{ mysql_root_password }}"
    
    - name: 사용자 생성 및 권한 부여
      mysql_user:
        name: "{{ mysql_user }}"
        password: "{{ mysql_password }}"
        priv: "{{ mysql_db }}.*:ALL"
        host: '%'
        state: present
        login_user: root
        login_password: "{{ mysql_root_password }}"
    
    - name: MySQL 서비스 시작 및 활성화
      systemd:
        name: mysql
        state: started
        enabled: yes
```

### 6.3 Docker 설치 및 컨테이너 실행

```yaml
---
- name: Docker 설치 및 설정
  hosts: docker_servers
  become: yes
  
  tasks:
    - name: 필요한 패키지 설치
      apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present
        update_cache: yes
    
    - name: Docker GPG 키 추가
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present
    
    - name: Docker 저장소 추가
      apt_repository:
        repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present
    
    - name: Docker 설치
      apt:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
        state: present
        update_cache: yes
    
    - name: Docker 서비스 시작 및 활성화
      systemd:
        name: docker
        state: started
        enabled: yes
    
    - name: 사용자를 docker 그룹에 추가
      user:
        name: "{{ ansible_user }}"
        groups: docker
        append: yes
    
    - name: Nginx 컨테이너 실행
      docker_container:
        name: nginx
        image: nginx:latest
        state: started
        ports:
          - "80:80"
        volumes:
          - /var/www/html:/usr/share/nginx/html:ro
        restart_policy: always
```

### 6.4 Role 사용 예제

**Role 구조 생성**
```bash
ansible-galaxy init roles/nginx
```

**roles/nginx/tasks/main.yml**
```yaml
---
- name: Nginx 설치
  apt:
    name: nginx
    state: present
    update_cache: yes
  when: ansible_os_family == "Debian"

- name: Nginx 설정 파일 생성
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    mode: '0644'
  notify: restart nginx

- name: Nginx 서비스 시작 및 활성화
  systemd:
    name: nginx
    state: started
    enabled: yes
```

**roles/nginx/handlers/main.yml**
```yaml
---
- name: restart nginx
  systemd:
    name: nginx
    state: restarted
```

**roles/nginx/defaults/main.yml**
```yaml
---
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_http_port: 80
```

**Playbook에서 Role 사용**
```yaml
---
- name: 웹서버 설정
  hosts: webservers
  become: yes
  roles:
    - role: nginx
      vars:
        nginx_http_port: 8080
```

### 6.5 조건부 작업 및 에러 처리

```yaml
---
- name: 안전한 업데이트 및 설정
  hosts: all
  become: yes
  
  tasks:
    - name: 시스템 정보 수집
      setup:
      register: system_info
    
    - name: 디스크 공간 확인
      shell: df -h / | tail -1 | awk '{print $5}' | sed 's/%//'
      register: disk_usage
      changed_when: false
    
    - name: 디스크 공간 부족 경고
      debug:
        msg: "경고: 디스크 사용률이 {{ disk_usage.stdout }}%입니다"
      when: disk_usage.stdout | int > 80
    
    - name: 패키지 업데이트 (Debian 계열)
      apt:
        upgrade: dist
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: 패키지 업데이트 (RedHat 계열)
      yum:
        name: "*"
        state: latest
      when: ansible_os_family == "RedHat"
    
    - name: 중요한 서비스 재시작
      block:
        - name: Nginx 재시작
          systemd:
            name: nginx
            state: restarted
          when: "'nginx' in system_info.ansible_facts.services"
      
      rescue:
        - name: 재시작 실패 시 알림
          debug:
            msg: "Nginx 재시작에 실패했습니다. 수동으로 확인하세요."
      
      always:
        - name: 서비스 상태 확인
          systemd:
            name: nginx
          register: nginx_status
          ignore_errors: yes
        
        - name: 상태 출력
          debug:
            msg: "Nginx 상태: {{ nginx_status.status.ActiveState }}"
```

---

## 7. 고급 기능

### 7.1 Vault (암호화)

**Vault 파일 생성**
```bash
ansible-vault create group_vars/all/vault.yml
```

**Vault 파일 편집**
```bash
ansible-vault edit group_vars/all/vault.yml
```

**Vault 파일 내용 보기**
```bash
ansible-vault view group_vars/all/vault.yml
```

**Vault 파일 사용**
```yaml
# group_vars/all/vault.yml
---
vault_mysql_root_password: mysecretpassword
vault_api_key: secret-api-key-12345
```

**Playbook에서 사용**
```yaml
vars:
  mysql_password: "{{ vault_mysql_root_password }}"
```

**실행 시**
```bash
ansible-playbook playbook.yml --ask-vault-pass
# 또는
ansible-playbook playbook.yml --vault-password-file ~/.vault_pass
```

### 7.2 Facts 수집 최적화

```yaml
---
- name: Facts 수집 비활성화
  hosts: all
  gather_facts: no
  
  tasks:
    - name: 필요한 Facts만 수집
      setup:
        gather_subset:
          - network
          - hardware
```

### 7.3 병렬 실행

```bash
# 10개 호스트를 동시에 실행
ansible-playbook playbook.yml -f 10

# 특정 호스트만 실행
ansible-playbook playbook.yml --limit webservers

# 특정 호스트 제외
ansible-playbook playbook.yml --limit 'all:!dbservers'
```

### 7.4 체크 모드 (Dry Run)

```bash
# 실제 변경 없이 실행 (시뮬레이션)
ansible-playbook playbook.yml --check

# 체크 모드에서 diff 보기
ansible-playbook playbook.yml --check --diff
```

### 7.5 콜백 플러그인

**ansible.cfg 설정**
```ini
[defaults]
stdout_callback = yaml
# 또는
stdout_callback = json
```

---

## 8. 실무 팁 및 모범 사례

### 8.1 디렉토리 구조 권장사항
```
project/
├── ansible.cfg
├── inventory/
│   ├── production
│   ├── staging
│   └── group_vars/
│       ├── all.yml
│       ├── webservers.yml
│       └── dbservers.yml
├── playbooks/
│   ├── site.yml
│   ├── webservers.yml
│   └── dbservers.yml
├── roles/
│   ├── common/
│   ├── nginx/
│   └── mysql/
├── files/
└── templates/
```

### 8.2 ansible.cfg 최적화
```ini
[defaults]
inventory = inventory/production
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 86400
stdout_callback = yaml
deprecation_warnings = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False
```

### 8.3 변수 우선순위
1. 명령줄 변수 (`-e`)
2. Playbook의 `vars`
3. `host_vars/`
4. `group_vars/`
5. Role의 `vars/`
6. Role의 `defaults/`
7. Inventory 변수

### 8.4 성능 최적화
- `gather_facts: no` 사용 (필요할 때만)
- Facts 캐싱 활성화
- 병렬 실행 (`-f` 옵션)
- `async` 및 `poll` 사용 (긴 작업)

### 8.5 보안 모범 사례
- SSH 키 기반 인증 사용
- Vault로 민감 정보 암호화
- 최소 권한 원칙 (become_user 지정)
- Inventory 파일 권한 관리
- 정기적인 Ansible 업데이트

---

## 9. 자주 사용하는 명령어

### 9.1 Ad-hoc 명령
```bash
# 패키지 설치
ansible webservers -m apt -a "name=nginx state=present" -b

# 서비스 재시작
ansible webservers -m systemd -a "name=nginx state=restarted" -b

# 파일 복사
ansible webservers -m copy -a "src=/local/file dest=/remote/file" -b

# 명령 실행
ansible webservers -m shell -a "df -h" -b

# Facts 확인
ansible webservers -m setup

# 호스트 연결 테스트
ansible webservers -m ping
```

### 9.2 Playbook 실행
```bash
# 기본 실행
ansible-playbook playbook.yml

# 특정 태그만 실행
ansible-playbook playbook.yml --tags "install,config"

# 특정 호스트만 실행
ansible-playbook playbook.yml --limit webservers

# 체크 모드
ansible-playbook playbook.yml --check

# 상세 출력
ansible-playbook playbook.yml -v
ansible-playbook playbook.yml -vv
ansible-playbook playbook.yml -vvv

# 병렬 실행
ansible-playbook playbook.yml -f 10

# Vault 비밀번호 입력
ansible-playbook playbook.yml --ask-vault-pass
```

### 9.3 Role 관리
```bash
# Role 생성
ansible-galaxy init roles/role_name

# Galaxy에서 Role 설치
ansible-galaxy install username.role_name

# Role 목록 보기
ansible-galaxy list

# Role 제거
ansible-galaxy remove username.role_name
```

---

## 10. 문제 해결

### 10.1 일반적인 에러

#### SSH 연결 실패
```bash
# 문제: Host key verification failed
# 해결: ansible.cfg에 추가
host_key_checking = False

# 또는 known_hosts에 추가
ssh-keyscan hostname >> ~/.ssh/known_hosts
```

#### 권한 문제
```yaml
# become: yes 추가
- name: 작업
  become: yes
  task: ...
```

#### Python 버전 문제
```yaml
# Inventory에 Python 경로 지정
[webservers]
web1 ansible_python_interpreter=/usr/bin/python3
```

### 10.2 디버깅 방법

```yaml
# 변수 값 확인
- name: 변수 출력
  debug:
    var: variable_name

# 메시지 출력
- name: 디버그 메시지
  debug:
    msg: "현재 값: {{ variable_name }}"

# Facts 확인
- name: Facts 출력
  debug:
    var: ansible_facts
```

```bash
# 상세 로그로 실행
ansible-playbook playbook.yml -vvv

# 특정 호스트만 실행하여 테스트
ansible-playbook playbook.yml --limit test-server
```

---

## 11. 참고 자료

- **공식 문서**: https://docs.ansible.com/
- **모듈 문서**: https://docs.ansible.com/ansible/latest/modules/modules_by_category.html
- **Ansible Galaxy**: https://galaxy.ansible.com/
- **Jinja2 템플릿**: https://jinja.palletsprojects.com/

---

## 12. 요약 체크리스트

### 기본 개념
- [ ] Inventory 이해
- [ ] Playbook 구조 이해
- [ ] Module 사용법
- [ ] Role 개념

### 문법
- [ ] 변수 사용
- [ ] 조건문 (when)
- [ ] 반복문 (loop)
- [ ] 템플릿 (Jinja2)
- [ ] Handler 사용

### 실무
- [ ] 패키지 설치/관리
- [ ] 파일/디렉토리 관리
- [ ] 서비스 관리
- [ ] 사용자/그룹 관리
- [ ] Vault 사용

### 고급
- [ ] Role 작성
- [ ] Facts 최적화
- [ ] 에러 처리
- [ ] 성능 최적화

---

## 13. Rocky Linux 9 기반 3대 VM 실습 시나리오 & 테스트 로드맵

### 13.1 시나리오 개요
- **VM 구성**
  - `vm-control`: Ansible Control Node (Rocky 9, Python3, Ansible 설치)
  - `vm-web`: 웹 애플리케이션 서버 (Nginx + Gunicorn, 방화벽/SSL 설정)
  - `vm-db`: 데이터베이스 서버 (MariaDB, 백업/모니터링)
- **네트워크**
  - 동일 서브넷, SSH 키 기반 접근
  - firewalld 사용, 서비스별 포트 정책 (HTTP 80/443, DB 3306)
- **실무 포인트**
  - SELinux enforcing 모드 유지, 필요한 정책만 허용
  - System role로 공통 튜닝, 개별 role로 서비스 구성

### 13.2 사전 준비 (Day 0)
| 단계 | 주요 작업 | Ansible 기능 |
| --- | --- | --- |
| 0-1 | Rocky 9 미러 업데이트, `dnf update -y` | `dnf`, `reboot`, `wait_for` |
| 0-2 | `ansible` 사용자 생성, sudo 권한, SSH 키 배포 | `user`, `authorized_key`, `copy` |
| 0-3 | SELinux enforcing 확인, firewalld zone 구성 | `selinux`, `firewalld` |
| 0-4 | `ansible.cfg`, Inventory (`inventory/rocky.yml`) 정리 | `template`, `ini_file` |

### 13.3 단계별 로드맵 (Day 1~3)

#### 단계 1: Inventory & 연결 검증
- **목표**: 인벤토리 그룹 (`control`, `web`, `db`, `common`) 구성, ping 테스트
- **구현 포인트**
  - YAML 인벤토리 + `group_vars/all.yml`에 공통 변수 정의
  - `ansible -i inventory/rocky.yml all -m ping`으로 기본 연결 검증
- **활용 기능**: `ping`, `setup`, `limit`, `check mode`

#### 단계 2: 공통 Base Role 배포 (`roles/base`)
- **내용**: 시스템 튜닝, 패키지/타임존/chrony, 로그 정책, fail2ban
- **테스트**
  - `chronyc sources`, `timedatectl` 결과 검증
  - `/etc/profile.d/security.sh` 등 공통 스크립트 반영 확인
- **Ansible 기능**: Role 구조, Handler (chronyd restart), `lineinfile`, `blockinfile`, `notify`, `tags`

#### 단계 3: 서비스 Role 배포
| Role | 대상 | 주요 작업 | Ansible 기능 |
| --- | --- | --- | --- |
| `roles/web` | `vm-web` | Nginx 설치, TLS/Let's Encrypt, Gunicorn systemd, 애플리케이션 배포 | `dnf`, `template`, `systemd`, `unarchive`, `set_fact`, `loop` |
| `roles/db` | `vm-db` | MariaDB 10.x, 사용자/권한, backup 스크립트, SELinux booleans | `mysql_user`, `mysql_db`, `cron`, `seboolean`, `file` |
| `roles/app` | `vm-web` | Python venv, `.env` 템플릿, migrations | `pip`, `shell`, `environment`, `become_user` |

- **검증**: `curl http://vm-web`, `mysql -h vm-db`

#### 단계 4: 모니터링/로그 (실무 시나리오)
- `roles/monitor`: node_exporter, process-exporter, 로그 로테이션, firewalld 서비스 추가
- `roles/alert`: webhook 스크립트 배포, systemd timer (로그 사이즈/백업 체크)
- **Ansible 기능**: `get_url`, `unarchive`, `template`, `systemd`, `cron`, `async/poll`, `register` + `when`

#### 단계 5: 운영 편의 기능
- **Vault**: DB 비밀번호, API 토큰 암호화 (`group_vars/all/vault.yml`)
- **조건 분기**: `when: inventory_hostname in groups['web']`
- **템플릿 고급 기능**: jinja2 filters, `to_nice_yaml`, `lookup`
- **재배포 전략**: `--tags "app"` / `--skip-tags "db"` / `--limit vm-web`
- **롤백**: `block/rescue`, `backup: yes`, `ansible.builtin.snapshot` (선택)

### 13.4 실행 로드맵 예시
1. `ansible-playbook playbooks/00_base.yml -i inventory/rocky.yml`
2. `ansible-playbook playbooks/10_web.yml --limit vm-web`
3. `ansible-playbook playbooks/20_db.yml --limit vm-db --ask-vault-pass`
4. `ansible-playbook playbooks/30_monitor.yml -f 5`
5. `ansible-playbook playbooks/40_app.yml --tags "deploy" --check`

### 13.5 검증 & 모의 장애 대응
- **체크리스트**
  - 구성 완료 후 `ansible web -m service_facts`로 서비스 상태 점검
  - `ansible db -m shell -a 'mysql -e "show databases;"' -b`로 DB 상태
  - 모니터/로그 Role 재실행 시 멱등성 확인 (`--check --diff`)
- **장애 시나리오**
  - Nginx conf 오류 → Handler 재시작 실패 → `rescue` 블록 알림 → 수정 후 `--tags config`
  - DB 포트 차단 → firewalld 규칙 수정 → `notify` → `reboot` + `wait_for`

### 13.6 실무 팁
- **병렬성**: `-f 10`, 단 `serial` 옵션으로 순차 배포 제어
- **stage별 Inventory**: `inventory/staging.yml`, `inventory/prod.yml` → `ansible.cfg`에서 분리
- **테스트 자동화**: `assert` 모듈로 주요 설정 검증
- **로그**: callback plugin yaml/json, `ANSIBLE_STDOUT_CALLBACK`

> 위 로드맵을 따라가면 Rocky Linux 9 환경에서 Ansible의 핵심 기능(Inventory/Role/Handler/Vault/조건/템플릿/async 등)을 단계별로 실습하며, 실무 운영에 필요한 구성을 폭넓게 경험할 수 있습니다.


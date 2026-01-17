#!/usr/bin/env python3
"""
AutoGLM Alibaba Cloud Orchestrator.
Generates configuration and instructs the Agent to setup GitHub Secrets.
"""

import subprocess
import os
import secrets
import sys

def generate_ssh_keypair(comment="GithubActions") -> tuple[str, str]:
    """Generates an Ed25519 SSH Key pair."""
    print("🔐 Generating SSH Key Pair for Alibaba ECS...")

    pub_key_path = os.path.expanduser("~/.ssh/github_alibaba_ecs.pub")
    priv_key_path = os.path.expanduser("~/.ssh/github_alibaba_ecs")

    # Generate keys using subprocess
    cmd = f"ssh-keygen -t ed25519 -C '{comment}' -f {priv_key_path}"
    subprocess.run(cmd, shell=True, check=True)

    with open(pub_key_path, 'r') as f:
        pub_key = f.read()

    with open(priv_key_path, 'r') as f:
        priv_key = f.read()

    return pub_key, priv_key

def generate_setup_instructions(pub_key: str, ecs_host: str) -> str:
    """Generates the prompt for the AutoGLM Agent."""

    return f"""
    [ENABLE PRESERVED THINKING MODE]
    We need to setup the Dual-Agent CI/CD Pipeline infrastructure for Alibaba Cloud ECS.

    Your task is to guide the user through the following steps via Chrome:

    STEP 1: Configure GitHub Secrets
    1. Open Chrome and navigate to: github.com/deedk822-lang/The-lab-verse-monitoring-/settings/secrets/actions
    2. Click 'New repository secret'
    3. Create the following secrets:
       - ECS_HOST: {ecs_host}
       - ECS_USER: root (or your specific user)
       - ECS_SSH_PRIVATE_KEY: [PASTE THE PRIVATE KEY GENERATED IN STEP BELOW]
       - ALIYUN_ACCESS_KEY_ID: [Get from Alibaba RAM Console]
       - ALIYUN_ACCESS_KEY_SECRET: [Get from Alibaba RAM Console]
       - ZAI_API_KEY: [Get from api.z.ai]
       - IFCLOUD_API_KEY: [Get from iflow.cloud for Qwen]

    STEP 2: Configure Alibaba ECS Server
    1. SSH into your Alibaba ECS instance: ssh root@{ecs_host}
    2. Run this initialization command:
       curl -sSL https://raw.githubusercontent.com/deedk822-lang/The-lab-verse-monitoring-/main/scripts/ecs-server-init.sh | bash
    3. Edit the .env file created on the server.

    STEP 3: Finalize SSH Connection
    1. On the ECS server, add the following public key to ~/.ssh/authorized_keys:

    {pub_key}

    2. Save and exit. Verify GitHub Actions can now connect.

    Report back when all secrets are added and the server is initialized.
    """

def main():
    # 1. Generate Keys
    pub, priv = generate_ssh_keypair()

    # 2. Get User Input for Host
    ecs_host = input("🌐 Enter your Alibaba ECS Public IP: ").strip()
    if not ecs_host:
        print("❌ Host IP is required.")
        sys.exit(1)

    # 3. Show Private Key to User
    print("\n" + "="*60)
    print("🔑 COPY THIS PRIVATE KEY TO GITHUB SECRET (ECS_SSH_PRIVATE_KEY):")
    print("="*60)
    print(priv)
    print("="*60)
    print("⚠️  Do not share this key publicly.\n")

    # 4. Generate Instructions for Agent
    instructions = generate_setup_instructions(pub, ecs_host)

    print("📝 Saving AutoGLM Instructions to file...")
    with open("autoglm_instructions.txt", "w") as f:
        f.write(instructions)

    print("✅ Setup Guide Generated: autoglm_instructions.txt")
    print("\nYou can now feed this file to the AutoGLM agent to guide the setup process.")

if __name__ == "__main__":
    main()

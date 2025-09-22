# 🚀 Flask + RDS Deployment on AWS Elastic Beanstalk

## 📖 Description
This project demonstrates how to deploy a **Flask web application** on **AWS Elastic Beanstalk (EB)** with a **MySQL RDS database** hosted in private subnets of a custom VPC.  

The architecture ensures **security and scalability** by:
- Hosting the **Flask app** in public subnets (accessible via Load Balancer).  
- Keeping **RDS private** (not exposed to the internet, only accessible from EB instances).  
- Managing traffic flow using **security groups** and **route tables**.  
- Deploying without a **NAT Gateway**, keeping costs minimal.  

This setup is ideal for small to medium applications that need a secure backend database and a scalable web app deployment.

---

## 🛠 Tech Stack

### **Backend**
- **Flask (Python)** → Lightweight web framework for API & app logic.  
- **PyMySQL** → Python client to connect Flask app with MySQL RDS.  

### **Database**
- **Amazon RDS (MySQL)** → Managed relational database, deployed in private subnets for security.  

### **Infrastructure (AWS)**
- **VPC (Virtual Private Cloud)** → Custom networking environment.  
- **Subnets** → Public (for EB) & Private (for RDS).  
- **Security Groups** → Firewall rules for EB, ALB, and RDS.  
- **Elastic Beanstalk (EB)** → Application deployment & scaling platform.  
- **Application Load Balancer (ALB)** → Distributes traffic to EB instances.  
- **Internet Gateway (IGW)** → Provides internet access to public subnets.  
- **Bastion Host (Optional)** → Secure access to RDS in private subnets.  

### **Others**
- **boto3 (optional)** → AWS SDK for Python (can fetch secrets/credentials).  
- **EB Extensions (.ebextensions)** → Custom configurations for environment variables & WSGI setup.  
- **cURL** → For API testing.  

---

## 🛠 Deployment Steps

### Step 1️⃣: Create VPC & Subnets

1. Go to **VPC → Your VPCs → Create VPC**
   - **Name:** project-vpc  
   - **IPv4 CIDR:** `10.0.0.0/16`  
   - **Tenancy:** Default  

2. Create subnets:
   - **Public-A:** `10.0.1.0/24` (AZ1)  
   - **Public-B:** `10.0.2.0/24` (AZ2)  
   - **Private-A:** `10.0.3.0/24` (AZ1)  
   - **Private-B:** `10.0.4.0/24` (AZ2)  

---

### Step 2️⃣: Internet Gateway & Route Tables

1. Create **IGW** → Attach to `project-vpc`.

2. **Public Route Table:**
   - Add route `0.0.0.0/0 → IGW`  
   - Associate: `Public-A`, `Public-B`

3. **Private Route Table:**
   - Associate: `Private-A`, `Private-B`  
   - ❌ No internet route needed  

➡️ EB instances will be in **public subnets**, RDS in **private subnets**.

---

### Step 3️⃣: Security Groups

- **SG-ALB (Load Balancer)**
  - **Inbound:** HTTP `80`, HTTPS `443` → `0.0.0.0/0`
  - **Outbound:** All

- **SG-EC2 (Elastic Beanstalk EC2)**
  - **Inbound:** HTTP `80` → SG-ALB  
  - SSH `22` → Your IP  
  - **Outbound:** All

- **SG-RDS (MySQL)**
  - **Inbound:** MySQL `3306` → SG-EC2 only  
  - **Outbound:** All  
  - *(Optional: allow MySQL `3306` from your IP for setup)*

---

### Step 4️⃣: Create RDS (Private)

1. **DB Subnet Group** → Add `Private-A`, `Private-B`  
   - **Name:** `project-db-subnet-group`

2. **RDS MySQL**
   - **DB Identifier:** `prodb`  
   - **Username:** `admin`  
   - **Password:** `admin123`  
   - **DB Class:** `db.t3.micro`  
   - **Public access:** ❌ No  
   - **Security group:** `SG-RDS`  
   - **Initial DB name:** `insured`

📌 Copy **RDS endpoint** → used in Flask.

---

### Step 5️⃣: Load DB Schema

### ✅ Option 1 (Temporary, less secure)
1. Add your IP in `SG-RDS` inbound.  
2. Run from your laptop:
    ```bash
    mysql -h <RDS-ENDPOINT> -u admin -p
   ```

3. Execute:
     ```bash
    CREATE DATABASE insured;
    USE insured;
    CREATE TABLE claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    policy_id VARCHAR(255),
    name VARCHAR(255),
    dob DATE,
    mobile VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ); 
   ```

### ✅ Option 2 (Preferred, secure via Bastion Host)
1. Launch Bastion EC2 in public subnet.
2. Allow SSH 22 from your IP.
3. Allow inbound 3306 from SG-Bastion → SG-RDS.
4. SSH into bastion:
    ```bash
    ssh -i ~/keys/mykey.pem ec2-user@<BASTION_PUBLIC_IP>
     ```
5. Install MySQL client:
    ```bash
    # Amazon Linux
    sudo dnf install -y mariadb105


    # Ubuntu
    sudo apt-get update && sudo apt-get install -y mysql-client
     ```

6. Connect:
    ```bash
    mysql -h <RDS-ENDPOINT> -u admin -p
    ```
7. Create schema (same SQL as above).

### Step 6️⃣: Prepare Flask App

### Folder structure:
    student-management-system/
    │
    ├── add_student.html        # Page to add new student
    ├── fetch_all_students.html # Page to view all students
    ├── index.html              # (Optional) Home page linking to add/view
    ├── scripts.js              # JS file for API     integration
    ├── README.md               # Project documentation
   
### Step 7️⃣: Zip the App
1. Zip contents only (not folder).
- Example:
   ```bash
   v1.zip → [application.py, requirements.txt, .ebextensions]
   ```

### Step 8️⃣: Deploy on Elastic Beanstalk

1. **EB → Create Application:**
- **Name:** flask-insured-app
- **Platform:** Python 3.x
- **Environment type:** Load balanced
- **Upload:** v1.zip

2. **Configure → Network:**
- **VPC:** project-vpc
- **LB Subnets:** Public-A, Public-B
- **EC2 Subnets:** Public-A, Public-B (auto-assign public IP)
- **ELB SG:** SG-ALB
- **EC2 SG:** SG-EC2
- **Key pair:** your SSH key
- **Roles:** default EB roles

3. **Launch environment** → wait 5–10 min.

### Step 9️⃣: Test App
1. Go to:
    ```bash
    http://<env>.elasticbeanstalk.com/
    ```
- / → ✅ Flask app running!
- /claims → returns [] initially

2. Add sample data:
    ```bash
    curl -X POST http://<EB-URL>/add-claim \
    -H "Content-Type: application/json" \
    -d '{"policy_id":"P1001","name":"Alice","dob":"1992-02-02","mobile":"9876543210"}'
    ```

## ✅ Final Working Flow:
1. **Elastic Beanstalk** EC2 instances in public subnets run Flask app.
2. **Application Load Balancer (ALB)** routes traffic to EB EC2 instances.
3. **Flask app** connects securely to **RDS MySQL** in private subnets.
4. **Security groups** restrict access:
- ALB ↔ EC2
- EC2 ↔ RDS
- SSH only from your IP

## 👨‍💻 Author
Khushal Ravindra Bhavsar✨  
🔗 [LinkedIn Profile](https://www.linkedin.com/in/khushal-bhavsar-/)  
🐙 [GitHub](https://github.com/Khushal41)
- Full Stack MERN Developer | Python & Cloud Enthusiast  
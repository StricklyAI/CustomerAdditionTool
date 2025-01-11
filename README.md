# Customer Data Processing and Ansible Playbook for Panorama

## **Overview**
This repository provides a solution for processing customer data files and creating network objects in a Palo Alto Networks Panorama device using an Ansible playbook. The solution supports both manual and file-based customer data input and securely handles credentials using Ansible Vault.

---

## **Features**

### **Customer Data Processing Script**
- Accepts input from CSV or Excel files (without headers).
- Supports manual data entry mode.
- Validates IP addresses and subnet masks.
- Automatically generates unique object names by removing spaces and apostrophes from customer names.
- Maps service codes to tags.
- Generates a YAML file containing customer network objects for use with Ansible.

### **Ansible Playbook**
- Uses the `panos` Ansible modules to interact with Panorama.
- Loads the generated customer YAML file.
- Configures address objects in Panorama.
- Commits the configuration to Panorama.
- Pushes the configuration to a specified firewall device.

---

## **How to Use**

### **Step 1: Process Customer Data**
1. Run the `customer_data_processing.py` script.
2. Provide the path to your CSV or Excel file, or choose to enter data manually.
3. The script will validate the input and generate a `customers_<name>_<timestamp>.yml` file.

```bash
python customer_data_processing.py
```

### **Step 2: Prepare the Ansible Environment**
1. Install the necessary Ansible collections:
   ```bash
   ansible-galaxy collection install paloaltonetworks.panos
   ```
2. Ensure your Ansible inventory file (`hosts`) includes the Panorama device.

Example:
```ini
[panorama]
panorama_ip ansible_host=192.168.1.1
```

### **Step 3: Secure Credentials with Ansible Vault**
1. Create an encrypted file to store your Panorama credentials:
   ```bash
   ansible-vault create panorama_credentials.yml
   ```
2. Add your credentials to the file:
   ```yaml
   panorama_credentials:
     ip_address: "192.168.1.1"
     username: "admin"
     password: "your_password"
   ```
3. Reference the credentials file in your playbook:

```yaml
vars_files:
  - panorama_credentials.yml
```

### **Step 4: Run the Ansible Playbook**
1. Run the playbook with the encrypted credentials:
   ```bash
   ansible-playbook panorama_playbook.yml --ask-vault-pass
   ```

---

## **File Structure**
```
.
├── customer_data_processing.py  # Main data processing script
├── panorama_playbook.yml        # Ansible playbook
├── panorama_credentials.yml     # Encrypted credentials file
├── customers_*.yml              # Generated customer files
└── README.md                    # Documentation
```

---

## **YAML File Example**
Generated customer YAML file:
```yaml
customers:
  - CustomerName: "Family Mart"
    CustomerIPAddress: "192.168.1.1"
    IPSubnetMask: "24"
    Tags: ["Retail"]
    ObjectName: "familymart_192.168.1.1_24"
  - CustomerName: "Sam's Club"
    CustomerIPAddress: "10.0.0.1"
    IPSubnetMask: "24"
    Tags: ["Wholesale"]
    ObjectName: "samsclub_10.0.0.1_24"
```

---

## **Best Practices for Using Ansible Vault**
- Use `ansible-vault encrypt` to secure sensitive files.
- Always use the `--ask-vault-pass` option when running playbooks to avoid exposing passwords.
- Regularly rotate your credentials to maintain security.

---

## **Future Enhancements**
- Add support for more object types (e.g., address groups, services).
- Include automated validation of Panorama configurations.
- Expand error handling and logging for both the script and playbook.


import pandas as pd
import yaml
import os
import ipaddress
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    filename='customer_processing.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def subnet_mask_to_cidr(subnet_mask):
    return ipaddress.IPv4Network(f"0.0.0.0/{subnet_mask}").prefixlen

def generate_object_name(name, ip_address, subnet_mask):
    cidr = subnet_mask_to_cidr(subnet_mask)
    return f"{name}_{ip_address}_{cidr}"

def validate_customer_data(customers):
    validated_customers = []
    object_names = set()  # Track object names to avoid duplicates

    for customer in tqdm(customers, desc="Validating", unit="customer"):
        name = customer.get('CustomerName', '').strip()
        ip_address = customer.get('CustomerIPAddress', '').strip()
        subnet_mask = customer.get('IPSubnetMask', '').strip()
        tags = customer.get('Tags', '')

        object_name = generate_object_name(name, ip_address, subnet_mask)

        if object_name in object_names:
            logging.warning(f"Duplicate object name '{object_name}' detected. Skipping.")
            continue
        object_names.add(object_name)

        customer['ObjectName'] = object_name
        customer['Tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        validated_customers.append(customer)

    return validated_customers

def main():
    file_path = input("Enter the path to the Excel or CSV file: ").strip()
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
    customers = df.to_dict(orient='records')
    validated_customers = validate_customer_data(customers)

    with open('customers.yml', 'w') as file:
        yaml.dump({'customers': validated_customers}, file)

    print("Customer data successfully saved to customers.yml.")

if __name__ == "__main__":
    main()

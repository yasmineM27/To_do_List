import { exec } from 'child_process';
import { promises as fs } from 'fs';
import util from 'util';

const execPromise = util.promisify(exec);

async function setupProject() {
  console.log("Setting up TaskFlow project...");
  
  try {
    // Create requirements.txt
    const requirements = `
Django==4.2.9
django-crispy-forms==2.1.0
crispy-tailwind==0.5.0
python-dotenv==1.0.0
Pillow==10.1.0
    `.trim();
    
    await fs.writeFile('requirements.txt', requirements);
    console.log("Created requirements.txt");
    
    console.log("Project setup complete!");
    console.log("\nTo get started with this project, you would run:");
    console.log("1. python -m venv venv");
    console.log("2. source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)");
    console.log("3. pip install -r requirements.txt");
    console.log("4. python manage.py migrate");
    console.log("5. python manage.py createsuperuser");
    console.log("6. python manage.py runserver");
  } catch (error) {
    console.error("Error setting up project:", error);
  }
}

setupProject();

## Setting Up Environment Variables

To configure the environment variables for the project, follow these steps:

1. Create a `.env` file in the root directory of the project.
2. Add the following lines to your `.env` file:
 SENDER_EMAIL=your_email@example.com
 SENDER_PASSWORD=your_password
 SMTP_SERVER=smtp.example.com
 SMTP_PORT=587

Replace `your_email@example.com` and `your_password` with your actual email credentials.

Note: If you're deploying on Streamlit Cloud, you can set these environment variables directly in the Streamlit dashboard under *Secrets* instead of creating a `.env` file.

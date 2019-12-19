Group Members:

Lucy Jiao (lucyjiao@college.harvard.edu)
Karina Wang (karinawang@college.harvard.edu)
Vineet Gangireddy (vineetgangireddy@college.harvard.edu)

Title of Project:

PCal: Your Period Pal

Purpose: To log and predict period cycles for a user given user-inputted symptoms and recommend ways to appease these symptoms

Documentation:
Inside the folder ‘pcal’ should be two folders - static/ and templates/ - and five other files: application.py, DESIGN.md, helpers.py, pcal.db, and README.md.

Inside static/, there is the styles.css file and six media files. The purpose of these files is for the formatting and aesthetics of the website. The media files include a music soundtrack that is autoplayed on the homepage, a .ico file that is the logo for our website, and various pictures that are used as backdrops throughout the website. The functions inside style.css create many features like text formatting, background colors, navigation bar, button design, etc. They are called upon from the html templates.

Inside templates/, there are all of our HTML files, including apology.html, calendar.html, calendarapology.html, layout.html, login.html, recommendations.html, register.html, symptoms.html, and today.html. The HTML file layout.html contains the basic HTML formatting for all of our pages, providing links and formatting for the navigation bar and containing the footer and header of all of our HTML pages. Each other HTML page within the folder templates/ extends this layout.html file and adds code onto it that performs the function that that specific webpage is intended for. In apology.html, there is code for displaying an apology to a user when an error occurs. In calendar.html, there is code for a date picker. In calendarapology.html, if there are no symptoms recorded on the date picked, it displays the page again with an alert at the top. In login.html, it contains a form asking for the user’s login information. In recommendations.html, there is code for displaying recommendations given input from application.py. In register.html, there is code for a form for the user to input a username, password, cycle length, and past cycle. In symptoms.html, there is code for a form for the user to input his or her symptoms on a current day. In today.html, there is code to display the user’s symptoms and prediction information. All of the files in templates/ are necessary for compiling and configuring our website.

In application.py, the following methods are called:
	today()
	symptoms()
	average()
	calendar()
	recommendations()
	login()
	register()
	calculate_cycle_length()


In helpers.py, the following methods are called:
	apology(message, code=400)
	currentday()

The database where user data is stored is called pcal.db.

Overall, in order to actually compile our website, all of the above files must be downloaded and placed together in one folder. Follow the following procedure in the terminal to launch the website once you have downloaded and created folders containing the above files:
$ cd project
$ cd pcal
$ ls
application.py  helpers.py        static/
pcal.db      templates/
README.md    DESIGN.md
$ export API_KEY=pk_794eb7aa754a4152a361a00516a251fb
$ flask run
After running these commands in the terminal, click on the link that is outputted in the terminal to launch the website.

Now, once the website is launched, you should see a page prompting you to login as well as a header and a navigation bar with the options of logging in and registering.

In order to access the rest of the website, you must first register yourself by clicking on the ‘Register’ tab at the top right and inputting a username, a password, a password confirmation, the usual cycle length of your period (if you do not know, you do not have to input; it will default to a 28 day period), and the day on which your last cycle started (defaults to today, if nothing is entered).

Now that you have registered, you can login using the username and password you inputted in the registration form. Once logged in, you should be able to see the homepage on which a soundtrack automatically plays, your next period start date and ovulation cycle start date is shown, and you are prompted to click on a link to enter your symptoms of the day.

In order to input symptoms for the day, click on the link called “Add Symptoms”. This link will take you to a form that asks for your stress level, pain level, and energy level from 1 to 4 (1 is the lowest and 4 is the highest), as well as emotions, additional notes, and a dropdown for flow level. When you fill out this form, you should be redirected to the homepage where you should now be able to see your symptoms on display above the “Add Symptoms” button. If your symptoms change throughout the day, you can click the button and fill out the form again, and your symptoms for that day will update.

Once you have input symptoms for the day, you can see recommendations based on these symptoms and symptoms of past days by clicking on the ‘Recommendations’ tab at the top. You will be redirected to a page that displays a recommendation for stress, pain, energy, and bleeding.

Finally, the last aspect of our website is the calendar tab. If you click the ‘Calendar’ tab, you will see a date picking form that allows you to choose a date. When you enter a specific date in the form, you should be able to see the symptoms that you recorded on a specific day. If there are no symptoms on the day that you have chosen, the ‘Calendar’ page will be reloaded and will include an alert this time saying that there were no symptoms recorded on that day, so choose another date.

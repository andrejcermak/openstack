from requests import post

print(post("http://127.0.0.1:5000/", json={"token": "eyJqa3UiOiJodHRwczpcL1wvbG9naW4uY2VzbmV0LmN6XC9vaWRjXC9qd2siLCJraWQiOiJyc2ExIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJkYmMyM2Q2ZGJkNTU0YmU2NTkxMTQxMTdlZmQ0ZmFmMGY1NzQ2NmY0QGVpbmZyYS5jZXNuZXQuY3oiLCJhenAiOiJmYTA0MGY5ZS1hZTViLTRmYzItOWNlYS03ZmFiNjcxMmM3NzMiLCJzY29wZSI6ImVkdVBlcnNvbkVudGl0bGVtZW50IGZvcndhcmRlZEVudGl0bGVtZW50IG9wZW5pZCBvZmZsaW5lX2FjY2VzcyBwcm9maWxlIGVkdV9wZXJzb25fZW50aXRsZW1lbnRzIGVtYWlsIiwiaXNzIjoiaHR0cHM6XC9cL2xvZ2luLmNlc25ldC5jelwvb2lkY1wvIiwiZXhwIjoxNTY2MjAyNjE4LCJpYXQiOjE1NjYxOTkwMTgsImp0aSI6ImQwZGMxNDEyLWE0YTEtNDBiMC1hN2M4LTA2MjRlY2E3MjUwNCJ9.JhjJ_cI3lZDorWQdLIEZO6aB7c7djpXz9ja76jMpjUNQ4MQcsPCZGxsiQy3zaAQD0X3Yn7cRsLXt4HmuKGTk5yxan9hhBnIKbIcB8wMhdSj88EL1T0c39_dNTeB8v0lRSnaWm6ArKRM3bFzOYbROM5kmbGCbX4wrs9psRa0M_4KhxgaVWYFc3PZON3YzEyx--HciqJWRgB-moYtTi7Est6I6W7EUYEMLwB7p_7J6_GwRwZ5QItSAkyFe96uOVxzmOYEIe2AswQfj0QWOKdUu4a5XC-_RQEfc9d3PpQM-NMNAgFLOMXwjtykv3KWo-WUrL9SJYFK23cQUta1LsqDBXw"}).headers)

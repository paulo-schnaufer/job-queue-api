create table clients (
id INTEGER primary key generated always as identity,
name VARCHAR(30) not null ,
api_key VARCHAR(255) not null,
rpm_limit INT,
created_at TIMESTAMP default CURRENT_TIMESTAMP not null
);

create table jobs (
id INTEGER primary key generated always as identity,
client_id INT references clients(id) not null,
status VARCHAR(20) default 'pending' not null,
payload JSONB not null,
result TEXT,
try_counter INT default 0 not null,
created_at TIMESTAMP default CURRENT_TIMESTAMP not null,
updated_at TIMESTAMP default CURRENT_TIMESTAMP not null,

check (status in ('pending', 'running', 'done', 'failed'))
);

create table job_logs (
id INTEGER primary key generated always as identity,
job_id INT REFERENCES jobs(id) not null,
event_timestamp TIMESTAMP default CURRENT_TIMESTAMP not null,
message TEXT not null
);
import boto3
import botocore
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []
    if(project):
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()
    print(instances)
    return instances

@click.group()
def cli():
    """Shotty manages snapshots """

# sub group volumes
@cli.group('volumes')
def volumes():
    """Commands for volumes """
@volumes.command('list')
@click.option('--project', default=None, help='only volumes for project(tag Porject:<name>)')

def list_volumes(project):
    "List Volumes for this instance"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            print(','.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + 'GiB',
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return




# define snapshot group
@cli.group('snapshots')
def snapshots():
    """Commnads for snapshots """

# define the snappy group functions
@snapshots.command('list')
@click.option('--project', default=None, help='only snapshots for the project')
def list_snapshots(project):
    "List Snapshots for the instances"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(','.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))
    return



# sub group Instances
@cli.group()
def instances():
    """ Commands for Instances """

# define instances sub group functions
@instances.command('list')
@click.option('--project', default=None, help='only instance for project(tag Project:<name>)')

def list_instances(project):
    "List EC2 Instances"
    instances = filter_instances(project)

    for i in instances:
        tags = {t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
            )))
    return

@instances.command('stop')
@click.option('--project', default=None, help='Only instances for the Project')
def stop_instances(project):
    "stop instances"
    instances = filter_instances(project)

    for i in instances:
        print('Stopping {0}...'.format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Cloud not stop {0} ".format(i.id) + str(e))
            continue
    return

@instances.command('start')
@click.option('--project', default=None, help='Only instances for the Project')
def start_instances(project):
    "start EC2 Instances"
    instances = filter_instances(project)

    for i in instances:
        print('Starting {0}'.format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Cloud not start {0} ".format(i.id) + str(e))
            continue
    return

@instances.command('terminate')
@click.option('--project', default=None, help='only Instances for the project')
def terminate_instances(project):
    "terminate instances"
    instances = filter_instances(project)
    for i in instances:
        print('Terminating {0}'.format(i.id))
        i.terminate()
    return

@instances.command('snapshot', help="Create snapshots of all volumes")
@click.option('--project', default=None, help='Only create snpashots for instances for project')
def create_snapshots(project):
    "Create snapshots for Ec2 instances volumes"

    instances = filter_instances(project)
    for i in instances:
        i.stop() # stop the instance before take snapshot
        print("Stopping instance {0}".format(i.id))
        i.wait_until_stopped()
        for v in i.volumes.all():
            print("Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by snapshot function from shotty")
        print("starting instance {0}".format(i.id))
        i.start()
        i.wait_until_running()
        print('instance ${0} is running now, and snapshot complete'.format(i.id))

    print("job done")
    return



if __name__ == '__main__':
    cli()

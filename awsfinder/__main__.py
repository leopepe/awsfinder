from operator import itemgetter
import boto3
import click


class EC2InstanceFinder:
    """ EC2 Instance Client Class

    """
    def __init__(self, region_name: str='us-east-1', profile_name: str=None):
        """

        :param region_name: Default region us-east-1 Virginia
        :param profile_name: Default None
        """
        self._region_name = region_name

        if profile_name:
            self._session = boto3.session.Session(region_name=self._region_name, profile_name=profile_name)
        else:
            self._session = boto3.session.Session(region_name=self._region_name)

        self.ec2 = self._session.resource('ec2')

    @staticmethod
    def get_id(instances: list):
        return [
            instance.instance_id
            for instance in instances
        ]

    @staticmethod
    def get_private_ip(instances: list):
        return [
            instance.private_ip_address
            for instance in instances
        ]

    def get_instance_by_tag(self, tag_key: str, tag_value: str) -> list:
        try:
            instances = self.ec2.instances.filter(Filters=[
                {'Name': 'tag:'+tag_key, 'Values': [tag_value]},
                {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
            ])
        except KeyError:
            instances = 'Tag {} or Value {} not found'.format(tag_key, tag_value)

        return instances


class EC2AmiFinder:
    """ EC2 AMI Client Class

    """

    def __init__(self, region_name: str='us-east-1', profile_name: str=None):
        # default region us-east-1 virginia
        self._region_name = region_name

        if profile_name:
            self._session = boto3.session.Session(region_name=self._region_name, profile_name=profile_name)
        else:
            self._session = boto3.session.Session(region_name=self._region_name)

        self.ec2 = self._session.resource('ec2')
        # self.images = self.ec2.images.all()
        self.instances = []

    @staticmethod
    def exclude_last(amis: list, last: int=3) -> list:
        """ Receives a list and return a slice of [last:]

        :param amis: list containing the AMIS
        :param last:
        :return:
        """
        return amis[last:]

    @staticmethod
    def get_last(amis: list, last: int=3) -> list:
        """ Receives a list and return a slice of [:last]

        :param amis:
        :param last:
        :return:
        """
        return amis[:last]

    @staticmethod
    def get_id(amis: list) -> list:
        """ Receives a list of tuples (name, version, id) and returns only the ids, ami[2]

        :param amis:
        :return:
        """
        ids = []
        for ami in amis:
            if len(ami) == 3:
                ids.append(ami[2])
            else:
                ids.append('No id {}'.format(ami))
        return ids

    def get_owned_amis(self, tag_keys: list=['version']) -> object:
        """

        :type tag_keys: list
        :rtype: object
        :return: list of ec2.Images
        """
        try:
            return self.ec2.images.filter(Owners=['self'], Filters=[{'Name': 'tag-key', 'Values': tag_keys}]).all()
        except IOError as e:
            raise 'Error retrieving owned images: {}'.format(e)

    def get_ami_by_version(self, name: str, version: str) -> object:
        """

        :param name: tag:Name value to Filters()
        :param version: tag:Version value to Filters()
        :type name: object
        """
        try:
            return self.ec2.images.filter(Filters=[
                {'Name': 'tag:Name', 'Values': [name]},
                {'Name': 'tag:version', 'Values': [version]}]).all()
        except IOError as e:
            raise 'Error retrieving images {}'.format(e)

    def get_ami_by_name(self, name):
        """

        :param name:
        :return:
        """
        try:
            return self.ec2.images.filter(Filters=[
                {'Name': 'tag:Name', 'Values': [name]}]).all()
        except IOError as e:
            raise 'Error retrieving images {}'.format(e)

    def get_amis_sorted_by_date(self, amis: list=None, reverse: bool=True):
        """

        :param amis:
        :param reverse:
        :return:
        """
        if not amis:
            amis = self.get_owned_amis()

        return sorted(
            [
                (ami.name, tag['Value'], ami.id, ami.creation_date)
                for ami in amis
                for tag in ami.tags
                if (tag['Key'] == 'version' and tag['Value'] != '')
            ],
            key=itemgetter(0, 3), reverse=reverse)

    def get_amis_sorted_by_version(self, amis: list=None, reverse: bool=True):
        """

        :param amis:
        :param reverse:
        :return:
        """
        if not amis:
            amis = self.get_owned_amis()

        print([(ami.name, tag['Value'], ami.id, ami.creation_date) for ami in amis for tag in ami.tags if (tag['Key'] == 'version' and tag['Value'] != '') ])
        return sorted(
            [
                (ami.name, tag['Value'], ami.id, ami.creation_date)
                for ami in amis
                for tag in ami.tags
                if (tag['Key'] == 'version' and tag['Value'] != '')
            ],
            key=itemgetter(0, 3), reverse=reverse)

    def get_amis_inuse(self):
        resp = self.ec2.instances.filter(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': [
                        'pending',
                        'running',
                        'shutting-down',
                        'stopping',
                        'stopped'
                    ]
                }
            ]
        )

        amis = [
            (self.ec2.Image(instance.image_id), tag['Value'], instance.image_id)
            for instance in resp
            for tag in instance.tags
        ]
        return amis

    def delete_ami_by_id(self, ami_id: str):
        """

        :param ami_id:
        :return:
        """
        try:
            return self.ec2.deregister_image(ami_id)
        except IOError as e:
            return 'Error: {}'.format(e)

    def delete_old_amis(self, keep_last: int=3):
        """

        :param keep_last:
        :return:
        """
        pass


@click.group()
@click.version_option()
def cli():
    """ amifinder

    amifinder is a tool to find amis by tag:Name and tag:version
    """


@cli.group()
def ami():
    """ AMI submenu"""


@ami.command('ls')
@click.option('--name', '-n', help='Filter AMI by tag Name', default=None)
# @click.option('--latest_ami_version', '-e', help='Return the latest AMI version', is_flag=True, default=False)
@click.option('--exclude_latest', '-x', help='Return the latest AMIs', type=int, default=0)
@click.option('--only_latest', '-l', help='Return the latest AMIs', type=int, default=0)
@click.option('--ids', help='Print only the id', is_flag=True, default=False)
@click.option('--exclude_inuse', help='Exclude the AMIs inuse by any instance', is_flag=True, default=False)
@click.option('--output', '-o', help='Output format: [json|text]', type=click.Choice(['json', 'text']), default='json')
def ami_ls(name, exclude_latest, only_latest, ids, exclude_inuse, output):
    ec2 = EC2AmiFinder()
    amis = ec2.get_amis_sorted_by_version(amis=ec2.get_ami_by_name(name))
    result = None
    # exclude last amis from search or list only the latest
    if exclude_latest:
        amis = ec2.exclude_last(amis=amis, last=exclude_latest)

    if only_latest:
        amis = ec2.get_last(amis=amis, last=only_latest)

    if exclude_inuse:
        amis = set(amis) - set(ec2.get_amis_inuse())

    # if latest_ami_version:
    #     amis = ec2.get_last(amis=amis, last=1)

    # print only the ids or tuple (name, version, id)
    if ids:
        result = ec2.get_id(amis)
    else:
        result = amis

    if output == 'text':
        result = ' '.join(str(ami) for ami in amis)

    click.echo(result)


@cli.group()
def instance():
    """ Instance submenu"""


@instance.command('ls')
@click.option('--tag_key', '-k', help='Filter Instances by tag key', default=None)
@click.option('--tag_value', '-v', help='Filter Instances by tag value', default=None)
@click.option('--ips', '-i', help='Get instances ip addresses', is_flag=True, default=False)
@click.option('--output', '-o', help='Output format: [json|text]', type=click.Choice(['json', 'text']), default='json')
@click.option('--reverse', help='Revert order of output', is_flag=True, default=False)
def instance_ls(tag_key, tag_value, ips, output, reverse):
    ec2 = EC2InstanceFinder()
    result = ec2.get_instance_by_tag(tag_key, tag_value)

    if ips:
        result = ec2.get_private_ip(result)
        if reverse and len(result) > 1:
            result.reverse()

    if output == 'text':
        result = ' '.join(str(ip) for ip in result)

    click.echo(result)


@cli.group()
def discover():
    """ Instance submenu"""


@discover.command('ami')
@click.option('--name', '-n', help='Filter AMI by tag Name', default=None)
@click.option('--latest_version', '-l', help='Discover AMI latest version', is_flag=True, default=False)
@click.option('--next_version', '-x', help='Displays the next version expected for AMI release', type=click.Choice(['major', 'minor', 'patch']), default='patch')
def discover_ami(name, latest_version, next_version):
    ec2 = EC2AmiFinder()
    amis = ec2.get_amis_sorted_by_date(amis=ec2.get_ami_by_name(name))
    result = None
    if latest_version:
        result = ec2.get_amis_sorted_by_date(amis=ec2.get_ami_by_name(name))[0]
    elif next_version:
        # major, minor, patch = ec2.get_last(amis=amis, last=1).pop()[1].split('.')
        major = int(ec2.get_last(amis=amis, last=1).pop()[1].split('.')[0])
        minor = int(ec2.get_last(amis=amis, last=1).pop()[1].split('.')[1])
        patch = int(ec2.get_last(amis=amis, last=1).pop()[1].split('.')[2])
        if next_version == 'major':
            major += 1
            minor = 0
            patch = 0
        elif next_version == 'minor':
            minor += 1
            patch = 0
        elif next_version == 'patch':
            patch += 1
        result = f'{major}.{minor}.{patch}'

    click.echo(result)


if __name__ == '__main__':
    cli()
